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

"""Test the specifics of SQLite-based repositories."""

import os
import os.path
import sqlite3
import tempfile
from datetime import timedelta

import pytest

from ..base import Repository
from ..sqlite import SqliteRepository, SqliteRepositoryFactory
from ...models import Grouping, Permission, User, UserKey
from ...utils import now


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


def test_memory_always_other_repository() -> None:
    """The factory will always return another repository for in-memory SQLite."""
    factory = SqliteRepositoryFactory("sqlite:")
    repo_1 = factory.create()
    assert repo_1 is not None
    repo_2 = factory.create()
    assert repo_2 is not None
    assert repo_1 != repo_2
    repo_1.close()
    repo_2.close()


def test_real_always_other_repository() -> None:
    """The factory will always return another repository for real SQLite."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    try:
        temp_file.close()
        factory = SqliteRepositoryFactory("sqlite://" + temp_file.name)
        repo_1 = factory.create()
        assert repo_1 is not None
        repo_2 = factory.create()
        assert repo_2 is not None
        assert repo_1 != repo_2
        repo_1.close()
        repo_2.close()
    finally:
        os.unlink(temp_file.name)
    assert not os.path.exists(temp_file.name)


def test_memory_initialize():
    """Initialize a memory-based repository."""
    factory = SqliteRepositoryFactory("sqlite:")
    assert factory.initialize()
    assert factory.initialize()  # Doing it twice does not harm
    repository = factory.create()
    user = repository.set_user(User(None, "user"))
    assert user.key is not None
    assert user.ident == "user"
    user_2 = repository.get_user(user.key)
    assert user == user_2


def test_memory_no_initialize(monkeypatch):
    """Test for error in initializing memory-based repositories."""
    def return_false(_):
        return False
    monkeypatch.setattr(SqliteRepositoryFactory, "_connect", return_false)
    factory = SqliteRepositoryFactory("sqlite:")
    assert factory.initialize() is False


def get_repository() -> Repository:
    """Create an initialized repository."""
    factory = SqliteRepositoryFactory("sqlite:")
    factory.initialize()
    return factory.create()


class MockCursor:
    """Simple cursor that returns something."""

    def fetchone(self):  # pylint: disable=no-self-use
        """Return one tuple."""
        return (1,)

    def close(self):
        """Close the mock cursor."""


def raise_exception(_self, sql: str, _values):
    """Mock method that substitutes SqliteRepository._execute."""
    if sql.startswith("SELECT "):
        return MockCursor()
    raise sqlite3.IntegrityError("Unknown")


def test_insert_user(monkeypatch):
    """Check that inserting a user can raise an exception."""
    repository = get_repository()
    user_1 = repository.set_user(User(None, "user_1"))
    user_2 = repository.set_user(User(None, "user_2"))

    monkeypatch.setattr(SqliteRepository, "_execute", raise_exception)
    with pytest.raises(sqlite3.IntegrityError):
        repository.set_user(User(None, "admin"))
    with pytest.raises(sqlite3.IntegrityError):
        repository.set_user(user_2._replace(ident=user_1.ident))


def make_grouping(code: str, host_key: UserKey) -> Grouping:
    """Create a grouping with a specific code for a specific host user."""
    yet = now()
    return Grouping(
        None, code, "grp", host_key, yet - timedelta(days=1),
        yet + timedelta(days=1), None, "RD", 5, 3, "nOt")


def test_set_grouping_exception(monkeypatch):
    """Check that setting a grouping will raise an exception."""
    repository = get_repository()
    host = repository.set_user(User(None, "host", Permission.HOST))
    grouping_1 = repository.set_grouping(make_grouping("code", host.key))
    grouping_2 = repository.set_grouping(make_grouping("abcd", host.key))

    monkeypatch.setattr(SqliteRepository, "_execute", raise_exception)
    with pytest.raises(sqlite3.IntegrityError):
        repository.set_grouping(make_grouping("xyz", host.key))
    with pytest.raises(sqlite3.IntegrityError):
        repository.set_grouping(grouping_2._replace(code=grouping_1.code))
