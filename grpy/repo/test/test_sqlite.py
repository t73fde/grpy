
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

"""Test the specifics of SQLite-based repositories."""

import os
import os.path
import tempfile

import pytest

from ..sqlite import SqliteRepositoryFactory


def test_scheme():
    """Only sqlite: is a valid URL scheme."""
    with pytest.raises(ValueError):
        SqliteRepositoryFactory("ram:")


def test_url() -> None:
    """The URL of the Factory is that of the init argument."""
    assert SqliteRepositoryFactory("sqlite:").url == "sqlite:"
    assert SqliteRepositoryFactory("sqlite://").url == "sqlite:"
    assert SqliteRepositoryFactory("sqlite:///").url == "sqlite:/"


def test_connect():
    """Connecting to an SQLite DB is possible, except for invalid file names."""
    assert SqliteRepositoryFactory("sqlite:").can_connect() is True
    assert SqliteRepositoryFactory("sqlite://./\0").can_connect() is False

    temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    try:
        assert SqliteRepositoryFactory("sqlite://" + temp_file.name).can_connect()
        temp_file.write(b"Hello World!\n")
        # assert not SqliteRepositoryFactory("sqlite://" + temp_file.name).can_connect()
    finally:
        temp_file.close()
        os.unlink(temp_file.name)
    assert not os.path.exists(temp_file.name)
    try:
        assert SqliteRepositoryFactory("sqlite://" + temp_file.name).can_connect()
    finally:
        os.unlink(temp_file.name)
    assert not os.path.exists(temp_file.name)
