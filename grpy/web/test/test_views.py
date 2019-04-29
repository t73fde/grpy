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

from ...core import utils
from ...core.models import Grouping, Registration, UserPreferences


def test_home_anonymous(client) -> None:
    """Test home view as an anonymous user."""
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert ": Home</title>" in data
    assert "Welcome!" in data
    assert url_for('home') in data
    assert url_for('about') in data
    assert url_for('auth.login') in data
    assert url_for('auth.logout') not in data


def test_home_host(client, auth, app_grouping: Grouping) -> None:
    """Test home view as a host."""
    auth.login("host")
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert "host</" in data
    assert url_for('grouping.detail', grouping_key=app_grouping.key) in data
    assert app_grouping.name in data
    assert str(app_grouping.final_date.minute) in data
    assert "Closed Groupings" not in data


def test_home_host_closed(app, client, auth, app_grouping: Grouping) -> None:
    """A closed grouping will be presented after active groupings."""
    url = url_for('home')
    auth.login("host")
    data = client.get(url).data.decode('utf-8')
    active_pos = data.find("Active Group")
    assert active_pos > 0
    assert active_pos < data.find(app_grouping.name)

    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.begin_date + datetime.timedelta(seconds=60),
        close_date=app_grouping.begin_date + datetime.timedelta(seconds=61)))
    data = client.get(url).data.decode('utf-8')
    active_pos = data.find("Active Group")
    assert active_pos > 0
    closed_pos = data.find("Closed Group")
    assert closed_pos > active_pos
    assert closed_pos < data.find(app_grouping.name)


def test_home_host_without_groupings(client, auth) -> None:
    """Test home view as a host without groupings."""
    auth.login("host-0")
    response = client.get(url_for('home'))
    assert b'(None)' in response.data
    assert b"Welcome" not in response.data


def test_home_user(client, auth) -> None:
    """Test home view as a participant."""
    auth.login("user")
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
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
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert "Registered Groupings" in data
    assert register_url in data
    assert client.get(register_url).status_code == 200

    # Now change the final_date
    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.begin_date + datetime.timedelta(seconds=60)))
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
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

    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert "Groups" not in data
    assert "Member" not in data


def test_about_anonymous(client) -> None:
    """Test about view as an anonymous user."""
    response = client.get(url_for('about'))
    data = response.data.decode('utf-8')
    assert ": About</title>" in data
    assert url_for('home') in data
    assert url_for('about') in data
    assert url_for('auth.login') in data
    assert url_for('auth.logout') not in data


def test_shortlink_host(client, auth, app_grouping: Grouping) -> None:
    """Test home view as a host."""
    url = url_for('shortlink', code=app_grouping.code)

    auth.login("host")
    response = client.get(url)
    assert response.status_code == 200
    assert response.data.count(url.encode('utf-8')) == 1
    assert response.data.count(b"scale(8)") == 1

    response = client.get(url + "?scale=A")
    assert response.data.count(b"scale(8)") == 1

    response = client.get(url + "?scale=16")
    assert response.data.count(b"scale(16)") == 1

    response = client.get(url + "?scale=1")
    assert response.data.count(b"scale(2)") == 1


def test_shortlink(client, auth, app_grouping: Grouping) -> None:
    """Test home view as a non-host."""
    url = url_for('shortlink', code=app_grouping.code)
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == \
        "http://localhost/auth/login?next_url=%2F{}".format(app_grouping.code)

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
