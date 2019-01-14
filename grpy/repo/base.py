
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

"""Base definitions for repositories."""

from typing import Any, Dict, Iterator, Optional, Sequence

from grpy.models import Grouping, KeyType, User


WhereSpec = Dict[str, Any]
OrderSpec = Sequence[str]


class DuplicateKey(Exception):
    """Signal that a key is not unique."""


class NothingToUpdate(Exception):
    """Signal a missing data element, so that an update is not possible."""


class Repository:
    """Abstract repository."""

    def close(self) -> None:
        """Close the repository, store all permanent data."""
        raise NotImplementedError("Repository.close")

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        raise NotImplementedError("Repository.set_user")

    def get_user(self, key: KeyType) -> Optional[User]:
        """Return user for given primary key."""
        raise NotImplementedError("Repository.get_user")

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Return user for given username."""
        raise NotImplementedError("Repository.get_user_by_username")

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[User]:
        """
        Return an iterator of all or some users.

        If `where` is not None, only the users according to a specification are
        returned. The keys of `where` are composed of valid user attributes and
        a relation specification, separated by "__".  Relation specifications
        are one of: "eq", "ne", "ge", "gt", "lt", and "le".  Examples are:
        "username__eq", "is_host__eq", "key__ne".

        If `order` is not None, the result is sorted with respect to given
        keys. Keys are valid user attributes, optionally prefixed by "-" or
        "+".  If the prefix "-" is given, sorting is descending, else it is
        ascending. Examples: "username", "-username".
        """
        raise NotImplementedError("Repository.iter_users")

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        raise NotImplementedError("Repository.set_grouping")

    def get_grouping(self, key: KeyType) -> Grouping:
        """Return grouping with given key."""
        raise NotImplementedError("Repository.get_grouping")

    def get_grouping_by_code(self, code: str) -> Grouping:
        """Return grouping with given short code."""
        raise NotImplementedError("Repository.get_grouping_by_code")

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """
        Return an iterator of all or some groupings.

        See method `iter_users` for a detailed description of `where` and
        `order`.
        """
        raise NotImplementedError("Repository.iter_groupings")


class RepositoryFactory:
    """
    An abstract factory for repositories.

    Every factory is initialized with a parsed URL that specifies the concrete
    data source, e.g. a database or a database management system. The type of
    this parsed URL is `str`.
    """

    @property
    def url(self) -> str:
        """Return the configured URL to access the data store."""
        raise NotImplementedError("RepositoryFactory.url")

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        raise NotImplementedError("RepositoryFactory.can_connect.")

    def create(self):
        """Create and setup a repository."""
        raise NotImplementedError("RepositoryFactory.open")
