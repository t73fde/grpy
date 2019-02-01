
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
from typing import Iterator, Optional
from urllib.parse import urlparse

from .base import (
    OrderSpec, Repository, RepositoryFactory, WhereSpec)
from .models import UserGroup, UserRegistration
from .proxy import ProxyRepository
from ..models import Grouping, Groups, KeyType, Registration, User


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
        else:
            self._database = parsed_url.path
        self._repository = None

    def _connect(self) -> Optional[sqlite3.Connection]:
        """Connect to the database or return None."""
        database_name = self._database if self._database else ":memory:"
        try:
            return sqlite3.connect(database_name)
        except Exception:  # pylint: disable=broad-except
            return None

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        connection = self._connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master")
            connection.close()
            return True
        return False

    def create(self) -> Repository:
        """Create and setup a repository."""
        if self._database is None:
            if self._repository is None:
                self._repository = ProxyRepository(SqliteRepository(self._connect()))
            return self._repository
        return SqliteRepository(self._connect())


class SqliteRepository(Repository):
    """SQLite-based repository."""

    def __init__(self, connection):
        """Initialize the repository."""
        self._connection = connection

    def close(self):
        """Close the repository: nothing to do here."""

    def set_user(self, user: User) -> User:
        """Add / update the given user."""

    def get_user(self, key: KeyType) -> Optional[User]:
        """Return user with given key or None."""

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user with given ident, or None."""

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[User]:
        """Return an iterator of all or some users."""

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""

    def get_grouping(self, key: KeyType) -> Grouping:
        """Return grouping with given key."""

    def get_grouping_by_code(self, code: str) -> Grouping:
        """Return grouping with given short code."""

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all or some groupings."""

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""

    def get_registration(self, grouping: KeyType, participant: KeyType) -> Registration:
        """Return registration with given grouping and participant."""

    def count_registrations_by_grouping(self, grouping: KeyType) -> int:
        """Return number of registration for given grouping."""

    def delete_registration(self, grouping: KeyType, participant: KeyType) -> None:
        """Delete the given registration from the repository."""

    def iter_groupings_by_participant(
            self,
            participant: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all groupings the participant applied to."""

    def iter_user_registrations_by_grouping(
            self,
            grouping: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserRegistration]:
        """Return an iterator of user data of some participants."""

    def set_groups(self, grouping: KeyType, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""

    def get_groups(self, grouping: KeyType) -> Groups:
        """Get groups builded for grouping."""

    def iter_groups_by_user(
            self,
            user: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserGroup]:
        """Return an iterator of group data of some participants."""
