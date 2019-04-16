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

import dataclasses  # pylint: disable=wrong-import-order
import os
import os.path
import sqlite3
import tempfile
from datetime import timedelta
from typing import cast

import pytest

from ...models import (Grouping, Permissions, Registration, User, UserKey,
                       UserPreferences)
from ...utils import now
from ..sqlite import SqliteConnection, SqliteRepository


def test_scheme() -> None:
    """Only sqlite: is a valid URL scheme."""
    with pytest.raises(ValueError):
        SqliteRepository("ram:")


def test_url() -> None:
    """The URL of the repository is that of the init argument."""
    assert SqliteRepository("sqlite:").url == "sqlite:"
    assert SqliteRepository("sqlite://").url == "sqlite:"
    assert SqliteRepository("sqlite:///").url == "sqlite:/"


def test_connect() -> None:
    """Connecting to an SQLite DB is possible, except for invalid file names."""
    assert SqliteRepository("sqlite:").can_connect() is True
    assert SqliteRepository("sqlite://./\0").can_connect() is False

    temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    try:
        assert SqliteRepository("sqlite://" + temp_file.name).can_connect()
        temp_file.write(b"Hello World!\n")
        # assert not SqliteRepository("sqlite://" + temp_file.name).can_connect()
    finally:
        temp_file.close()
        os.unlink(temp_file.name)
    assert not os.path.exists(temp_file.name)
    try:
        assert SqliteRepository("sqlite://" + temp_file.name).can_connect()
    finally:
        os.unlink(temp_file.name)
    assert not os.path.exists(temp_file.name)


def test_memory_always_other_connection() -> None:
    """The repository will always return another connection for in-memory SQLite."""
    repository = SqliteRepository("sqlite:")
    connection_1 = repository.create()
    assert connection_1 is not None
    connection_2 = repository.create()
    assert connection_2 is not None
    assert connection_1 != connection_2
    connection_1.close(True)
    connection_2.close(True)


def test_real_always_other_connection() -> None:
    """The repository will always return another connection for real SQLite."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    try:
        temp_file.close()
        repository = SqliteRepository("sqlite://" + temp_file.name)
        connection_1 = repository.create()
        assert connection_1 is not None
        connection_2 = repository.create()
        assert connection_2 is not None
        assert connection_1 != connection_2
        connection_1.close(True)
        connection_2.close(False)
    finally:
        os.unlink(temp_file.name)
    assert not os.path.exists(temp_file.name)


def test_memory_initialize() -> None:
    """Initialize a memory-based repository."""
    repository = SqliteRepository("sqlite:")
    assert repository.initialize()
    assert repository.initialize()  # Doing it twice does not harm
    connection = repository.create()
    user = connection.set_user(User(None, "user"))
    assert user.key is not None
    assert user.ident == "user"
    user_2 = connection.get_user(user.key)
    assert user == user_2


def test_memory_no_initialize(monkeypatch) -> None:
    """Test for error in initializing memory-based repositories."""
    def return_false(_):
        return False
    monkeypatch.setattr(SqliteRepository, "_connect", return_false)
    repository = SqliteRepository("sqlite:")
    assert repository.initialize() is False


def test_failed_connection() -> None:
    """Test a connection that was not set-up properly."""
    conn = SqliteConnection(None)
    conn.close(False)
    with pytest.raises(TypeError):
        conn.close(True)


def get_connection() -> SqliteConnection:
    """Create an initialized repository."""
    repository = SqliteRepository("sqlite:")
    repository.initialize()
    return cast(SqliteConnection, repository.create())


class MockCursor:
    """Simple cursor that returns something."""

    def fetchone(self):  # pylint: disable=no-self-use
        """Return one tuple."""
        return (1,)

    def close(self):
        """Close the mock cursor."""


def raise_exception(_self, sql: str, _values):
    """Mock method that substitutes SqliteConnection._execute."""
    if sql.startswith("SELECT "):
        return MockCursor()
    raise sqlite3.IntegrityError("Unknown")


def test_insert_user(monkeypatch) -> None:
    """Check that inserting a user can raise an exception."""
    connection = get_connection()
    user_1 = connection.set_user(User(None, "user_1"))
    user_2 = connection.set_user(User(None, "user_2"))

    monkeypatch.setattr(SqliteConnection, "_execute", raise_exception)
    with pytest.raises(sqlite3.IntegrityError):
        connection.set_user(User(None, "admin"))
    with pytest.raises(sqlite3.IntegrityError):
        connection.set_user(dataclasses.replace(user_2, ident=user_1.ident))


def make_grouping(code: str, host_key: UserKey) -> Grouping:
    """Create a grouping with a specific code for a specific host user."""
    yet = now()
    return Grouping(
        None, code, "grp", host_key, yet - timedelta(days=1),
        yet + timedelta(days=1), None, "RD", 5, 3, "nOt")


def test_set_grouping_exception(monkeypatch) -> None:
    """Check that setting a grouping will raise an exception."""
    connection = get_connection()
    host = connection.set_user(User(None, "host", Permissions.HOST))
    assert host.key is not None
    grouping_1 = connection.set_grouping(make_grouping("code", host.key))
    grouping_2 = connection.set_grouping(make_grouping("abcd", host.key))

    monkeypatch.setattr(SqliteConnection, "_execute", raise_exception)
    with pytest.raises(sqlite3.IntegrityError):
        connection.set_grouping(make_grouping("xyz", host.key))
    with pytest.raises(sqlite3.IntegrityError):
        connection.set_grouping(dataclasses.replace(grouping_2, code=grouping_1.code))


class NotRegistered(UserPreferences):  # pylint: disable=too-few-public-methods
    """A preferences class that is not registered (and cannot be encoded)."""


def test_set_registration() -> None:
    """A registration preference that can't be encoded."""
    connection = get_connection()
    host = connection.set_user(User(None, "host", Permissions.HOST))
    assert host.key is not None
    grouping = connection.set_grouping(make_grouping("code", host.key))
    assert grouping.key is not None
    user = connection.set_user(User(None, "UsER"))
    assert user.key is not None

    registration = Registration(grouping.key, user.key, NotRegistered())
    connection.set_registration(registration)
    messages = connection.get_messages()
    assert len(messages) == 1
    assert messages[0].category == 'critical'
    assert messages[0].text.startswith("Unable to store preferences of type ")
    assert connection.get_registration(grouping.key, user.key) is None


def test_get_registration() -> None:
    """An inserted modified registration can't be retrieved."""
    connection = get_connection()
    host = connection.set_user(User(None, "host", Permissions.HOST))
    assert host.key is not None
    grouping = connection.set_grouping(make_grouping("code", host.key))
    assert grouping.key is not None
    user = connection.set_user(User(None, "UsER"))
    assert user.key is not None

    registration = Registration(grouping.key, user.key, UserPreferences())
    connection.set_registration(registration)
    assert registration == connection.get_registration(grouping.key, user.key)
    connection._execute(  # pylint: disable=protected-access
        "UPDATE registrations SET preferences=''")
    assert connection.get_registration(grouping.key, user.key) is None


def test_iter_user_registrations_by_grouping() -> None:
    """Iterate over all user data of registrations in case of decoding errors."""
    connection = get_connection()
    host = connection.set_user(User(None, "host", Permissions.HOST))
    assert host.key is not None
    grouping = connection.set_grouping(make_grouping("code", host.key))
    assert grouping.key is not None

    for i in range(7):
        user = connection.set_user(User(None, "user-%d" % i))
        assert user.key is not None
        connection.set_registration(Registration(
            grouping.key, user.key, UserPreferences()))

    assert len(list(connection.iter_user_registrations_by_grouping(grouping.key))) == 7
    connection._execute(  # pylint: disable=protected-access
        "UPDATE registrations SET preferences=''")
    assert not connection.iter_user_registrations_by_grouping(grouping.key)
