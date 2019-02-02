
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

"""SQLite-based repository."""

import sqlite3
import uuid
from typing import Iterator, Optional
from urllib.parse import urlparse

from .base import (
    OrderSpec, Repository, RepositoryFactory, WhereSpec)
from .models import UserGroup, UserRegistration
from ..models import Grouping, Groups, KeyType, Permission, Registration, User


class SqliteRepositoryFactory(RepositoryFactory):
    """Maintain a singleton RAM-based repository."""

    def __init__(self, repository_url: str):
        """Initialize the factory."""
        parsed_url = urlparse(repository_url)
        if parsed_url.scheme != "sqlite":
            raise ValueError(
                "SqliteRepositoryFactory cannot handle scheme: {}".format(
                    parsed_url.scheme))
        parsed_url = parsed_url._replace(
            netloc="", params='', query='', fragment='')
        super().__init__(parsed_url.geturl())

        if not parsed_url.path:
            self._database = None
            self._repository_class = SqliteMemoryRepository
        else:
            self._database = parsed_url.path
            self._repository_class = SqliteRepository
        self._connection: Optional[sqlite3.Connection] = None

    def _connect(self) -> Optional[sqlite3.Connection]:
        """Connect to the database or return None."""
        if self._database:
            try:
                return sqlite3.connect(self._database)
            except Exception:  # pylint: disable=broad-except
                return None

        if not self._connection:
            self._connection = sqlite3.connect(":memory:")
        return self._connection

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        connection = self._connect()
        if connection:
            connection.execute("SELECT name FROM sqlite_master")
            connection.close()
            return True
        return False

    def initialize(self) -> bool:
        """Initialize the repository, if needed."""
        connection = self._connect()
        if not connection:
            return False
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            tables = {row[0] for row in cursor.fetchall()}
            if "users" not in tables:
                cursor.execute("""
CREATE TABLE users(
    key TEXT PRIMARY KEY,
    ident TEXT UNIQUE NOT NULL,
    permission INT)
""")
        finally:
            cursor.close()
        return True

    def create(self) -> Repository:
        """Create and setup a repository."""
        return self._repository_class(self._connect())


class SqliteMemoryRepository(Repository):
    """SQLite-based and memory-based repository."""

    def __init__(self, connection):
        """Initialize the repository."""
        self._connection = connection

    def close(self):
        """Close the repository."""
        self._connection = None

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        user_key = uuid.uuid4()
        self._connection.execute(
            "INSERT INTO users VALUES(?,?,?)",
            (str(user_key), user.ident, user.permission.value))
        return user._replace(key=user_key)

    def get_user(self, user_key: KeyType) -> Optional[User]:
        """Return user with given key or None."""
        cursor = self._connection.execute(
            "SELECT ident, permission FROM users WHERE key=?", (str(user_key),))
        row = cursor.fetchone()
        return User(user_key, row[0], Permission(row[1]))

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user with given ident, or None."""

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[User]:
        """Return an iterator of all or some users."""

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""

    def get_grouping(self, grouping_key: KeyType) -> Optional[Grouping]:
        """Return grouping with given key."""

    def get_grouping_by_code(self, code: str) -> Optional[Grouping]:
        """Return grouping with given short code."""

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all or some groupings."""

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""

    def get_registration(
            self, grouping_key: KeyType, user_key: KeyType) -> Optional[Registration]:
        """Return registration with given grouping and user."""

    def count_registrations_by_grouping(self, grouping_key: KeyType) -> int:
        """Return number of registration for given grouping."""

    def delete_registration(self, grouping_key: KeyType, user_key: KeyType) -> None:
        """Delete the given registration from the repository."""

    def iter_groupings_by_user(
            self,
            user_key: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all groupings the user applied to."""

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserRegistration]:
        """Return an iterator of user data of some user."""

    def set_groups(self, grouping_key: KeyType, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""

    def get_groups(self, grouping_key: KeyType) -> Groups:
        """Get groups builded for grouping."""

    def iter_groups_by_user(
            self,
            user_key: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserGroup]:
        """Return an iterator of group data of some user."""


class SqliteRepository(SqliteMemoryRepository):
    """SQLite-based repository."""

    def close(self):
        """Close the repository."""
        self._connection.close()
        super().close()
