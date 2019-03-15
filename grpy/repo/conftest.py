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

"""Fixtures for testing the repository."""

import os
import tempfile
from datetime import timedelta

import pytest

from ..models import Grouping, Permissions, User
from ..utils import now
from . import create_repository

# pylint: disable=redefined-outer-name


@pytest.fixture(params=[
    "ram:",
    pytest.param("dummy:", marks=pytest.mark.safe),
    pytest.param("sqlite:", marks=pytest.mark.safe),
    pytest.param("sqlite:///", marks=pytest.mark.safe)])
def connection(request):
    """Provide an open connection."""
    if request.param == "sqlite:///":
        temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        temp_file.close()
        repository = create_repository("sqlite://" + temp_file.name)
    else:
        repository = create_repository(request.param)
        temp_file = None
        assert repository.url == request.param
    repository.initialize()

    connection = repository.create()
    yield connection

    assert not connection.get_messages()
    connection.close(True)
    if temp_file:
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
