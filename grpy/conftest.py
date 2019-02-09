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

"""Fixtures fpr testing."""

import os
import tempfile
from datetime import timedelta

from flask import url_for

import pytest

from .models import Grouping, Permission, User
from .repo import create_factory
from .repo.logic import set_grouping_new_code
from .utils import now
from .web.app import create_app


# pylint: disable=redefined-outer-name


@pytest.fixture(params=["ram:", "sqlite:", "sqlite:///"])
def app(request):
    """Create an app as fixture."""
    if request.param == "sqlite:///":
        temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        temp_file.close()
        repository_url = "sqlite://" + temp_file.name
    else:
        repository_url = request.param
        temp_file = None

    grpy_app = create_app({
        'TESTING': True,
        'REPOSITORY': repository_url,
        'AUTH_URL': None,
    })

    with grpy_app.test_request_context():
        connection = grpy_app.get_connection()
        connection.set_user(User(None, "host", Permission.HOST))
        connection.set_user(User(None, "host-0", Permission.HOST))

    yield grpy_app
    if temp_file:
        os.unlink(temp_file.name)


class AuthenticationActions:
    """Actions for Authentication, to be used as a fixture."""

    def __init__(self, client):
        """Initialize the object."""
        self._client = client

    def login(self, username: str, password: str = 'test') -> None:
        """Perform the login."""
        response = self._client.post(
            url_for('login'), data={'username': username, 'password': password})
        assert response.status_code == 302

    def logout(self) -> None:
        """Perform the logout."""
        self._client.get(url_for('logout'))


@pytest.fixture
def auth(client) -> AuthenticationActions:
    """Fixture for authentication."""
    return AuthenticationActions(client)


@pytest.fixture(params=["dummy:", "ram:", "sqlite:", "sqlite:///"])
def connection(request):
    """Provide an open connection."""
    if request.param == "sqlite:///":
        temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        temp_file.close()
        factory = create_factory("sqlite://" + temp_file.name)
    else:
        factory = create_factory(request.param)
        temp_file = None
        assert factory.url == request.param
    factory.initialize()

    repo = factory.create()
    yield repo

    repo.close(True)
    if temp_file:
        os.unlink(temp_file.name)


@pytest.fixture
def grouping(connection) -> Grouping:
    """Build a simple grouping object."""
    host = connection.get_user_by_ident("host")
    if not host:
        host = connection.set_user(User(None, "host", Permission.HOST))

    yet = now()
    return Grouping(
        None, ".code", "g-name", host.key, yet - timedelta(days=1),
        yet + timedelta(days=6), None, "RD", 7, 7, "")


@pytest.fixture
def app_grouping(app):
    """Insert a grouping into the repository."""
    yet = now()
    host = app.get_connection().get_user_by_ident("host")
    return set_grouping_new_code(app.get_connection(), Grouping(
        None, ".code", "g-Name", host.key, yet - timedelta(days=1),
        yet + timedelta(days=1), None, "RD", 17, 7, "Notizie"))
