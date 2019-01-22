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

"""Fixtures fpr testing."""

from datetime import timedelta

from flask import url_for

import pytest

from .models import Grouping, Permission, User
from .repo import create_factory
from .repo.logic import set_grouping_new_code
from .utils import now
from .web.app import create_app


# pylint: disable=redefined-outer-name


@pytest.fixture
def app():
    """Create an app as fixture."""
    grpy_app = create_app({'TESTING': True})

    with grpy_app.test_request_context():
        repository = grpy_app.get_repository()
        repository.set_user(User(None, "host", Permission.HOST))
        repository.set_user(User(None, "host-0", Permission.HOST))

    return grpy_app


@pytest.fixture
def client(app):
    """Create a test client as fixture."""
    with app.test_client() as test_client:
        yield test_client


class AuthenticationActions:
    """Actions for Authentication, to be used as a fixture."""

    def __init__(self, client):
        """Initialize the object."""
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
    """Fixture for authentication."""
    return AuthenticationActions(client)


@pytest.fixture(params=["dummy:", "ram:"])
def repository(request):
    """Provide an open repository."""
    factory = create_factory(request.param)
    assert factory.url == request.param
    repo = factory.create()
    yield repo
    repo.close()


@pytest.fixture
def grouping(repository) -> Grouping:
    """Build a simple grouping object."""
    host = repository.get_user_by_ident("host")
    if not host:
        host = repository.set_user(User(None, "host", Permission.HOST))

    yet = now()
    return Grouping(
        None, ".code", "g-name", host.key, yet - timedelta(days=1),
        yet + timedelta(days=6), None, "RD", 7, 7, "")


@pytest.fixture
def app_grouping(app):
    """Insert a grouping into the repository."""
    yet = now()
    host = app.get_repository().get_user_by_ident("host")
    return set_grouping_new_code(app.get_repository(), Grouping(
        None, ".code", "g-Name", host.key, yet, yet + timedelta(days=1),
        None, "RD", 17, 7, "Notizie"))
