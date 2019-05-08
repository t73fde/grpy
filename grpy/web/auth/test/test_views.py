##
#    Copyright (c) 2019 Detlef Stern
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

"""Test the web views for auth blueprint."""

import dataclasses
import itertools
from typing import cast

from flask import g, session, url_for

from ....core.models import (Grouping, Permissions, Registration, User,
                             UserKey, UserPreferences)
from ...app import GrpyApp
from ...test.common import (check_bad_anon_requests, check_flash, check_get,
                            check_get_data, check_message, check_redirect,
                            check_requests)


def check_bad_requests(client, auth, url: str, do_post: bool = True) -> None:
    """Assert that others cannot access resource."""
    auth.login('user')
    check_requests(client, url, 403, do_post)
    auth.login('host')
    check_requests(client, url, 403, do_post)
    check_bad_anon_requests(client, auth, url, do_post)


def test_login(client) -> None:
    """Test login view."""
    url = url_for('auth.login')
    assert client.get(url).status_code == 200
    response = client.post(url, data={'username': "host", 'password': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert session['user_identifier'] == "host"


def test_login_new_user(app: GrpyApp, client) -> None:
    """Test login view for new user."""
    response = client.post(
        url_for('auth.login'), data={'username': "new_user", 'password': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert session['user_identifier'] == "new_user"
    assert app.get_connection().get_user_by_ident("new_user") is not None


def test_invalid_login(app: GrpyApp, client) -> None:
    """Test login view for invalid login."""
    app.config['AUTH_URL'] = ""
    url = url_for('auth.login')
    response = client.post(url, data={'username': "xunknown", 'password': "1"})
    assert response.status_code == 200
    assert b"Cannot authenticate user" in response.data
    assert 'user_identifier' not in session


def test_double_login(client, auth) -> None:
    """A double login makes the last user to be logged in."""
    auth.login("user")
    assert session['user_identifier'] == "user"
    assert b"User &#39;user&#39; was logged out." in client.get(
        url_for('auth.login')).data
    auth.login("host")
    assert session['user_identifier'] == "host"


def test_name_change_after_login(app: GrpyApp, client, auth) -> None:
    """Username is changed after login."""
    auth.login("host")
    connection = app.get_connection()
    user = connection.get_user_by_ident("host")
    assert user is not None
    connection.set_user(dataclasses.replace(user, ident="tsoh"))
    client.get("/")
    assert g.user is None


def test_login_with_redirect(app: GrpyApp, client) -> None:
    """Test login view when redirect after successful login."""
    url = url_for('auth.login', next_url="/ABCDEF/")
    response = client.get(url)
    assert b'<input id="next_url" name="next_url" type="hidden" value="/ABCDEF/">' \
        in response.data

    response = client.post(
        url_for('auth.login'),
        data={'username': "new_user", 'password': "1", 'next_url': "/ABCDEF/"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/ABCDEF/"
    assert session['user_identifier'] == "new_user"
    assert app.get_connection().get_user_by_ident("new_user") is not None


def test_logout(client, auth) -> None:
    """Test login/logout sequence."""
    auth.login("host")
    assert session['user_identifier'] == "host"
    response = client.get(url_for('auth.logout'))
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert 'user_identifier' not in session


def test_logout_without_login(client) -> None:
    """A logout without previous login is ignored."""
    assert 'user_identifier' not in session
    response = client.get(url_for('auth.logout'))
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert 'user_identifier' not in session


def test_admin_users(app: GrpyApp, client, auth) -> None:
    """Only an admistrator is allowed to get this page."""
    url = url_for('auth.users')
    check_bad_requests(client, auth, url, False)

    auth.login("admin")
    data = check_get_data(client, url)
    assert url in data
    for user in app.get_connection().iter_users():
        assert str(user.key) in data
        assert user.ident in data


def test_admin_user_create(app: GrpyApp, client, auth) -> None:
    """Test the creation of new users."""
    url = url_for('auth.user_create')
    check_bad_requests(client, auth, url)

    auth.login('admin')
    check_get(client, url)

    response = client.post(url, data={})
    assert response.status_code == 200
    assert response.data.count(b'This field is required') == 1

    list_url = url_for('auth.users')
    check_redirect(client.post(url, data={'ident': "name3"}), list_url)
    user = app.get_connection().get_user_by_ident("name3")
    assert user is not None
    assert user.permissions == Permissions(0)
    assert user.last_login is None

    response = client.post(url, data={'ident': "name3"})
    assert response.status_code == 200
    check_message(client, "error", "Ident 'name3' is already in use.")


def test_admin_user_detail(app: GrpyApp, client, auth) -> None:
    """Only an administrator is allowed to read all user details."""
    admin_user = app.get_connection().get_user_by_ident("admin")
    assert admin_user is not None
    assert admin_user.key is not None

    for user in app.get_connection().iter_users():
        url = url_for('auth.user_detail', user_key=user.key)
        check_bad_requests(client, auth, url, False)
        auth.login("admin")
        data = check_get_data(client, url)
        assert "User " + user.ident in data
        if user.key == admin_user.key:
            assert " (You)" in data


def test_admin_change_permission(app: GrpyApp, client, auth) -> None:
    """An administrator can change permissions."""
    admin_user = app.get_connection().get_user_by_ident("admin")
    assert admin_user is not None
    assert admin_user.key is not None

    userlist_url = url_for('auth.users')
    auth.login("admin")
    for user in app.get_connection().iter_users():
        assert user.key is not None
        url = url_for('auth.user_detail', user_key=user.key)
        data = check_get_data(client, url)
        if user.key == admin_user.key:
            assert "Active" not in data
            assert "Administrator" not in data
        else:
            assert "Active" in data
            assert "Administrator" in data
        assert "Host" in data

        for is_active, is_host, is_admin in itertools.product((True, False), repeat=3):
            response = client.post(url, data={
                'active': "y" if is_active else "",
                'host': "y" if is_host else "",
                'admin': "y" if is_admin else "",
            })
            check_flash(
                client, response, userlist_url,
                "info", "Permissions of '{}' updated.".format(user.ident))
            new_user = app.get_connection().get_user(user.key)
            assert new_user is not None
            if user.key == admin_user.key:
                assert new_user.is_active
                assert new_user.is_admin
            else:
                assert new_user.is_active == is_active
                assert new_user.is_admin == is_admin
            assert new_user.is_host == is_host


def test_admin_user_detail_lists(
        app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Show that all user details are displayed."""
    assert app_grouping.key is not None
    users = [
        app.get_connection().set_user(User(None, "user-%d" % i)) for i in range(5)]
    assert users[0].key is not None
    url = url_for('auth.user_detail', user_key=users[0].key)
    auth.login("admin")

    app.get_connection().set_registration(Registration(
        app_grouping.key, users[0].key, UserPreferences()))
    data = check_get_data(client, url)
    assert "Hosted Groupings" not in data
    assert "Groups" not in data
    assert "Registered Groupings" in data
    assert app_grouping.name in data

    app.get_connection().set_groups(
        app_grouping.key, (frozenset([cast(UserKey, user.key) for user in users]),))
    data = check_get_data(client, url)
    assert "Hosted Groupings" not in data
    assert "Groups" in data
    assert "Registered Groupings" not in data
    assert app_grouping.name in data
    for user in users:
        assert user.ident in data

    app.get_connection().set_groups(app_grouping.key, ())
    app.get_connection().delete_registrations(app_grouping.key)
    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping, host_key=users[0].key))
    data = check_get_data(client, url)
    assert "Hosted Groupings" in data
    assert "Groups" not in data
    assert "Registered Groupings" not in data
    assert app_grouping.name in data
