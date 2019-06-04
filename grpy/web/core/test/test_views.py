##
#    Copyright (c) 2018,2019 Detlef Stern
#
#    This file is part of grpy - user grouping.
#
#    Grpy is free software: you can redistribute it and/or modify it under the
#    terms of the GNU Affero General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    Grpy is distributed in the hope that it will be useful, but WITHOUT ANY
#    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#    FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for
#    more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with grpy. If not, see <http://www.gnu.org/licenses/>.
##

"""Test the web views."""

import dataclasses
import datetime

from flask import url_for

from ....core import utils
from ....core.models import (Grouping, Permissions, Registration, User,
                             UserPreferences)
from ....version import Version
from ...app import GrpyApp
from ...test.common import check_get_data


def test_home_anonymous(client) -> None:
    """Test home view as an anonymous user."""
    data = check_get_data(client, url_for('home'))
    assert ": Home</title>" in data
    assert "Welcome!" in data
    assert url_for('home') in data
    assert url_for('about') in data
    assert url_for('auth.login') in data
    assert url_for('auth.logout') not in data


def test_home_host(client, auth, app_grouping: Grouping) -> None:
    """Test home view as a host."""
    auth.login("host")
    data = check_get_data(client, url_for('home'))
    assert "host</" in data
    assert url_for('grouping.detail', grouping_key=app_grouping.key) in data
    assert app_grouping.name in data
    assert str(app_grouping.final_date.minute) in data
    assert "Closed Groupings" not in data
    assert data.count(url_for('grouping.create')) == 1


def test_home_host_user(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """An user that was previously a host can view its groupings."""
    auth.login("host")

    # Make host a non-host
    connection = app.get_connection()
    user = connection.get_user_by_ident("host")
    assert user is not None
    user = connection.set_user(dataclasses.replace(user, permissions=Permissions(0)))
    assert user.is_active
    assert not user.is_host

    data = check_get_data(client, url_for('home'))
    assert url_for('grouping.detail', grouping_key=app_grouping.key) in data
    assert data.count(url_for('grouping.create')) == 0
    assert "Create" not in data


def test_home_host_closed(app, client, auth, app_grouping: Grouping) -> None:
    """A closed grouping will be presented after active groupings."""
    url = url_for('home')
    auth.login("host")
    data = check_get_data(client, url)
    active_pos = data.find("Active Group")
    assert active_pos > 0
    assert active_pos < data.find(app_grouping.name)

    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.begin_date + datetime.timedelta(seconds=60),
        close_date=app_grouping.begin_date + datetime.timedelta(seconds=61)))
    data = check_get_data(client, url)
    active_pos = data.find("Active Group")
    assert active_pos > 0
    closed_pos = data.find("Closed Group")
    assert closed_pos > active_pos
    assert closed_pos < data.find(app_grouping.name)


def test_home_host_without_groupings(app: GrpyApp, client, auth) -> None:
    """Test home view as a host without groupings."""
    app.get_connection().set_user(User(None, "host-0", Permissions.HOST))
    auth.login("host-0")
    response = client.get(url_for('home'))
    assert b'(None)' in response.data
    assert b"Welcome" not in response.data


def test_home_user(client, auth) -> None:
    """Test home view as a participant."""
    auth.login("user")
    data = check_get_data(client, url_for('home'))
    assert "user</" in data
    assert " valid grouping link " in data


def test_home_user_after_register(app, client, auth, app_grouping: Grouping) -> None:
    """Home view shows registration."""
    assert app_grouping.key is not None
    auth.login("user")
    user = app.get_connection().get_user_by_ident("user")
    assert user
    register_url = url_for('grouping.register', grouping_key=app_grouping.key)
    assert client.get(register_url).status_code == 200

    app.get_connection().set_registration(Registration(
        app_grouping.key, user.key, UserPreferences()))
    data = check_get_data(client, url_for('home'))
    assert "Registered Groupings" in data
    assert register_url in data
    assert client.get(register_url).status_code == 200

    # Now change the final_date
    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.begin_date + datetime.timedelta(seconds=60)))
    data = check_get_data(client, url_for('home'))
    assert "Registered Groupings" in data
    assert register_url not in data
    assert client.get(register_url).status_code == 302


def test_home_user_after_close(app, client, auth, app_grouping: Grouping) -> None:
    """Home view shows registration."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.begin_date + datetime.timedelta(seconds=60),
        close_date=app_grouping.begin_date + datetime.timedelta(seconds=61)))
    assert app_grouping.key is not None

    auth.login("user")
    user = app.get_connection().get_user_by_ident("user")
    assert user.key is not None
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))

    data = check_get_data(client, url_for('home'))
    assert "Groups" not in data
    assert "Member" not in data


def test_home_inactive(app: GrpyApp, client, auth) -> None:
    """An inactive user must be logged out."""
    url = url_for('home')
    login_url = url_for('auth.login')
    assert check_get_data(client, url).count(login_url) == 2
    auth.login("inactive")
    assert check_get_data(client, url).count(login_url) == 0

    # Make user inactive
    user = app.get_connection().get_user_by_ident("inactive")
    assert user is not None
    user = app.get_connection().set_user(dataclasses.replace(
        user, permissions=user.permissions | Permissions.INACTIVE))

    assert check_get_data(client, url).count(login_url) == 2


def test_about_anonymous(app: GrpyApp, client) -> None:
    """Test about view as an anonymous user."""
    app.version = Version("VeRsIoN", "VcS", "DaTe")
    data = check_get_data(client, url_for('about'))
    assert ": About</title>" in data
    assert url_for('home') in data
    assert url_for('about') in data
    assert url_for('auth.login') in data
    assert url_for('auth.logout') not in data
    assert "VeRsIoN" not in data
    assert "VcS" not in data
    assert "DaTe" not in data


def test_about_user(app: GrpyApp, client, auth) -> None:
    """An user can see some version details."""
    app.version = Version("VeRsIoN", "VcS", "DaTe")
    auth.login("user")
    data = check_get_data(client, url_for('about'))
    assert "VeRsIoN" in data
    assert "VcS" not in data
    assert "DaTe" not in data


def test_about_admin(app: GrpyApp, client, auth) -> None:
    """An administrator can see more version details."""
    app.version = Version("", "VcS", "DaTe")
    auth.login("admin")
    data = check_get_data(client, url_for('about'))
    assert "VeRsIoN" not in data
    assert "VcS" in data
    assert "DaTe" in data

    app.version = Version("VERsion", "", "")
    data = check_get_data(client, url_for('about'))
    assert "VERsion" in data
    assert "VcS" not in data
    assert "DaTe" not in data


def test_shortlink_host(client, auth, app_grouping: Grouping) -> None:
    """Test home view as a host."""
    url = url_for('shortlink', code=app_grouping.code)

    auth.login("host")
    data = check_get_data(client, url)
    assert data.count(url) == 1
    assert data.count("scale(8)") == 1

    assert check_get_data(client, url + "?scale=A").count("scale(8)") == 1
    assert check_get_data(client, url + "?scale=16").count("scale(16)") == 1
    assert check_get_data(client, url + "?scale=1").count("scale(2)") == 1


def test_shortlink(client, auth, app_grouping: Grouping) -> None:
    """Test home view as a non-host."""
    url = url_for('shortlink', code=app_grouping.code)
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == \
        f"http://localhost/auth/login?next_url=%2F{app_grouping.code}"

    auth.login("student")
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == \
        "http://localhost" + url_for('grouping.register', grouping_key=app_grouping.key)


def test_shortlink_after_final(app, client, auth, app_grouping: Grouping) -> None:
    """When final date is reached, no short link is possible."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping, final_date=utils.now() - datetime.timedelta(seconds=600)))
    url = url_for('shortlink', code=app_grouping.code)
    auth.login("host")
    assert client.get(url).status_code == 404
    auth.login("student")
    assert client.get(url).status_code == 404
