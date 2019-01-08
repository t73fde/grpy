
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

from flask import url_for

import pytest

from ..app import create_app
from ...models import Permission, User


@pytest.fixture
def app():
    """Create an app as fixture."""
    grpy_app = create_app({'TESTING': True})

    with grpy_app.test_request_context():
        repository = grpy_app.get_repository()
        repository.set_user(User(None, "host", Permission.HOST))

    return grpy_app


# pylint: disable=redefined-outer-name


@pytest.fixture
def client(app):
    """Create a test client as fixture."""
    with app.test_client() as test_client:
        yield test_client


class AuthenticationActions:
    """Actions for Authentication, to be used as a fixture."""

    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        """Perform the login."""
        response = self._client.post(
            url_for('login'), data={'username': username, 'password': password})
        assert response.status_code == 302

    def logout(self):
        """Perform the logout."""
        return self._client.get(url_for('logout'))


@pytest.fixture
def auth(client):
    """Authentication fixture."""
    return AuthenticationActions(client)
