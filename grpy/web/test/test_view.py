
##
#    Copyright (c) 2018 Detlef Stern
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

import datetime
import uuid

from flask import g, session, url_for

import pytest

from ..app import create_app
from ... import utils
from ...models import Grouping, Permission, User


@pytest.fixture
def app():
    """Create an app as fixture."""
    grpy_app = create_app({'TESTING': True})

    with grpy_app.test_request_context():
        repository = grpy_app.get_repository()
        repository.set_user(User(None, "host", Permission.HOST))
        repository.set_user(User(None, "user"))

    return grpy_app


# pylint: disable=redefined-outer-name


@pytest.fixture
def client(app):
    """Create a test client as fixture."""
    with app.test_client() as test_client:
        yield test_client


def test_home_anonymous(client):
    """Test home view as an anonymous user."""
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert ": Home</title>" in data
    assert "Welcome!" in data
    assert url_for('home') in data
    assert url_for('about') in data
    assert url_for('login') in data
    assert url_for('logout') not in data


def insert_simple_grouping(repository):
    """Insert a grouping into the repository."""
    now = utils.now()
    host = repository.get_user_by_username("host")
    return repository.set_grouping(Grouping(
        None, "Name-PM", host.key, now, now + datetime.timedelta(days=1), None,
        "RD", 17, 7, "Notizie"))


def test_home_host(app, client):
    """Test home view as a host."""
    repository = app.get_repository()
    grouping = insert_simple_grouping(repository)
    login(client, "host")
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert "host</span>" in data
    assert url_for('grouping_detail', key=grouping.key) in data
    assert grouping.name in data
    assert str(grouping.final_date.minute) in data


def test_home_user(client):
    """Test home view as a participant."""
    login(client, "user")
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert "user</span>" in data
    assert " valid grouping link " in data


def test_about_anonymous(client):
    """Test about view as an anonymous user."""
    response = client.get(url_for('about'))
    data = response.data.decode('utf-8')
    assert ": About</title>" in data
    assert url_for('home') in data
    assert url_for('about') in data
    assert url_for('login') in data
    assert url_for('logout') not in data


def test_login(client):
    """Test login view."""
    url = url_for('login')
    assert client.get(url).status_code == 200
    response = client.post(url, data={'username': "host", 'password': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert session['username'] == "host"


def test_invalid_login(client):
    """Test login view for invalid login."""
    url = url_for('login')
    response = client.post(url, data={'username': "unknown", 'password': "1"})
    assert response.status_code == 200
    assert b"Cannot authenticate user" in response.data
    assert 'username' not in session


def login(client, username: str, password: str = "1") -> None:
    """Perform the login."""
    response = client.post(
        url_for('login'), data={'username': username, 'password': password})
    assert response.status_code == 302


def test_double_login(client):
    """A double login makes the last user to be logged in."""
    login(client, "user")
    assert session['username'] == "user"
    assert b"User &#39;user&#39; was logged out." in client.get(url_for('login')).data
    login(client, "host")
    assert session['username'] == "host"


def test_name_change_after_login(app, client):
    """Username is changed after login."""
    login(client, "host")
    repository = app.get_repository()
    user = repository.get_user_by_username("host")
    repository.set_user(user._replace(username="tsoh"))
    client.get("/")
    assert g.user is None


def test_logout(client):
    """Test login/logout sequence."""
    login(client, "host")
    assert session['username'] == "host"
    response = client.get(url_for('logout'))
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert 'username' not in session


def test_logout_without_login(client):
    """A logout without previous login is ignored."""
    assert 'username' not in session
    response = client.get(url_for('logout'))
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert 'username' not in session


def test_grouping_detail(app, client):
    """Test grouping detail view."""
    repository = app.get_repository()
    grouping = insert_simple_grouping(repository)
    url = url_for('grouping_detail', key=grouping.key)
    response = client.get(url)
    assert response.status_code == 401

    login(client, "host")
    response = client.get(url)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert grouping.note in data

    login(client, "user")
    response = client.get(url)
    assert response.status_code == 403

    assert client.get(url_for('grouping_detail', key=uuid.uuid4())).status_code == 404
