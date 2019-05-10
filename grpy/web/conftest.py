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

"""Fixtures for testing the web application."""

import os
import tempfile
from datetime import timedelta
from typing import Any, Iterator, Sequence

import pytest
from flask import url_for

from ..core.models import Grouping, Permissions, User
from ..core.utils import now
from ..repo.logic import set_grouping_new_code
from .app import GrpyApp, create_app

pytest.register_assert_rewrite("grpy.web.test.common")

# pylint: disable=redefined-outer-name


def _create_app(repository_url) -> GrpyApp:
    """Create an app for testing and initialize the repository."""
    grpy_app = create_app({
        'TESTING': True,
        'REPOSITORY': repository_url,
        'AUTH_URL': None,
    })

    with grpy_app.test_request_context():
        connection = grpy_app.get_connection()
        connection.set_user(User(None, "host", Permissions.HOST))
        connection.set_user(User(None, "admin", Permissions.ADMIN))
        connection.set_user(User(None, "manager", Permissions.MANAGER))

    return grpy_app


def _get_request_param() -> Sequence[str]:
    """Return a list of parameters for app(request)."""
    if os.environ.get('SMOKE', ''):
        return ["ram:"]
    return [
        "ram:",
        pytest.param("sqlite:", marks=pytest.mark.safe),
        pytest.param("sqlite:///", marks=pytest.mark.safe),
    ]


@pytest.fixture(params=_get_request_param())
def app(request) -> Iterator[GrpyApp]:
    """Create an app as fixture."""
    if request.param == "sqlite:///":
        temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        temp_file.close()
        repository_url = "sqlite://" + temp_file.name
        with_tempfile = True
    else:
        repository_url = request.param
        with_tempfile = False

    yield _create_app(repository_url)
    if with_tempfile:
        os.unlink(temp_file.name)


@pytest.fixture
def ram_app() -> Iterator[GrpyApp]:
    """Create a RAM-based app as a fixture."""
    grpy_app = _create_app("ram:")
    with grpy_app.test_request_context():
        yield grpy_app


@pytest.fixture
def ram_client(ram_app: GrpyApp):
    """Create a RAM-based HTTP client object."""
    with ram_app.test_client() as client:
        yield client


class AuthenticationActions:
    """Actions for Authentication, to be used as a fixture."""

    def __init__(self, client: Any):
        """Initialize the object."""
        self.client = client

    def login(self, ident: str, password: str = 'test') -> None:
        """Perform the login."""
        response = self.client.post(
            url_for('auth.login'), data={'ident': ident, 'password': password})
        assert response.status_code == 302

    def logout(self) -> None:
        """Perform the logout."""
        self.client.get(url_for('auth.logout'))


@pytest.fixture
def auth(client) -> AuthenticationActions:
    """Fixture for authentication."""
    return AuthenticationActions(client)


@pytest.fixture
def ram_auth(ram_client) -> AuthenticationActions:
    """Fixture for RAM-based authentication."""
    return AuthenticationActions(ram_client)


@pytest.fixture
def app_grouping(app):
    """Insert a grouping into the repository."""
    yet = now()
    host = app.get_connection().get_user_by_ident("host")
    return set_grouping_new_code(app.get_connection(), Grouping(
        None, ".code", "g-Name", host.key, yet - timedelta(days=1),
        yet + timedelta(days=1), None, "RD", 17, 7, "Notizie"))
