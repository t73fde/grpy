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


def check_user_login(app: GrpyApp, ident: str):
    """Assert that user with given ident is logged in."""
    user = app.get_connection().get_user_by_ident(ident)
    assert user is not None
    assert user.key is not None
    assert session['user'] == user.key.int


def test_login(app: GrpyApp, client) -> None:
    """Test login view."""
    url = url_for('auth.login')
    assert client.get(url).status_code == 200
    response = client.post(url, data={'ident': "host", 'password': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    check_user_login(app, "host")


def test_login_new_user(app: GrpyApp, client) -> None:
    """Test login view for new user."""
    response = client.post(
        url_for('auth.login'), data={'ident': "new_user", 'password': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    check_user_login(app, "new_user")


def test_invalid_login(app: GrpyApp, client) -> None:
    """Test login view for invalid login."""
    app.config['AUTH_URL'] = ""
    url = url_for('auth.login')
    response = client.post(url, data={'ident': "xunknown", 'password': "1"})
    assert response.status_code == 200
    assert b"Cannot authenticate user" in response.data
    assert 'user' not in session


def test_double_login(app: GrpyApp, client, auth) -> None:
    """A double login makes the last user to be logged in."""
    auth.login("user")
    check_user_login(app, "user")
    assert b"User &#39;user&#39; was logged out." in client.get(
        url_for('auth.login')).data
    auth.login("host")
    check_user_login(app, "host")


def test_ident_change_after_login(app: GrpyApp, client, auth) -> None:
    """Ident is changed after login."""
    auth.login("host")
    connection = app.get_connection()
    user = connection.get_user_by_ident("host")
    assert user is not None
    connection.set_user(dataclasses.replace(user, ident="tsoh"))
    client.get("/")
    assert g.user.ident == "tsoh"


def test_user_delete_after_login(app: GrpyApp, client, auth) -> None:
    """Ident is changed after login."""
    auth.login("userdelete")
    connection = app.get_connection()
    user = connection.get_user_by_ident("userdelete")
    assert user is not None
    assert user.key is not None
    connection.delete_user(user.key)
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
        data={'ident': "new_user", 'password': "1", 'next_url': "/ABCDEF/"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/ABCDEF/"
    check_user_login(app, "new_user")


def test_logout(app: GrpyApp, client, auth) -> None:
    """Test login/logout sequence."""
    auth.login("host")
    check_user_login(app, "host")
    response = client.get(url_for('auth.logout'))
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert 'user' not in session


def test_logout_without_login(client) -> None:
    """A logout without previous login is ignored."""
    assert 'user' not in session
    response = client.get(url_for('auth.logout'))
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert 'user' not in session
