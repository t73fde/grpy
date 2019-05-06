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

from flask import g, session, url_for

from ...app import GrpyApp
from ...test.common import check_bad_anon_requests, check_get, check_requests


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
    response = check_get(client, url)
    data = response.data.decode("utf-8")
    assert url in data
    for user in app.get_connection().iter_users():
        assert str(user.key) in data
        assert user.ident in data


def test_admin_user_detail(app: GrpyApp, client, auth) -> None:
    """Only an administrator is allowed to read all user details."""
    admin_user = app.get_connection().get_user_by_ident("admin")
    assert admin_user is not None
    assert admin_user.key is not None

    for user in app.get_connection().iter_users():
        url = url_for('auth.user_detail', user_key=user.key)
        check_bad_requests(client, auth, url, False)
        auth.login("admin")
        response = check_get(client, url)
        data = response.data.decode('utf-8')
        assert ": " + user.ident in data
        if user.key == admin_user.key:
            assert " (You)" in data
