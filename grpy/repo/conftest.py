##
#    Copyright (c) 2019-2021 Detlef Stern
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

"""Fixtures for testing the repository."""

import os
import tempfile
from datetime import timedelta
from typing import Any, Sequence

import pytest

from ..core.models import Grouping, Permissions, User
from ..core.utils import now
from .base import Repository
from .dummy import DummyRepository
from .ram import RamRepository
from .sqlite import SqliteRepository


def _get_request_param() -> Sequence[Any]:
    """Return a list of parameters for connection(request)."""
    if os.environ.get('SMOKE', ''):
        return ["ram:"]
    return [
        "ram:",
        pytest.param("dummy:", marks=pytest.mark.safe),
        pytest.param("sqlite:", marks=pytest.mark.safe),
        pytest.param("sqlite:///", marks=pytest.mark.safe),
    ]


# pylint: disable=redefined-outer-name


@pytest.fixture(params=_get_request_param())
def connection(request):
    """
    Provide an open connection.

    Use the real repositories, and not the proxies, to allow for better
    assert messages.
    """
    if request.param == "sqlite:///":
        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as temp_file:
            temp_file_name = temp_file.name
        repository: Repository = SqliteRepository("sqlite://" + temp_file_name)
        with_tempfile = True
    else:
        if request.param == "ram:":
            repository = RamRepository(request.param)
        elif request.param == "dummy:":
            repository = DummyRepository(request.param)
        else:
            assert request.param == "sqlite:"
            repository = SqliteRepository("sqlite:")
        with_tempfile = False
        assert repository.url == request.param
    repository.initialize()

    connection = repository.create()
    yield connection

    connection.close(True)
    if with_tempfile:
        os.unlink(temp_file.name)


@pytest.fixture
def grouping(connection) -> Grouping:
    """Build a simple grouping object."""
    host = connection.get_user_by_ident("host")
    if not host:
        host = connection.set_user(User(None, "host", Permissions.HOST))

    yet = now()
    return Grouping(
        None, ".code", "g-name", host.key, yet - timedelta(days=1),
        yet + timedelta(days=6), None, "RD", 7, 7, "")
