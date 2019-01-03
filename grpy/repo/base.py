
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

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        raise NotImplementedError("Repository.set_user")

    def get_user(self, key: KeyType) -> Optional[User]:
        """Return user for given primary key."""
        raise NotImplementedError("Repository.get_user")

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Return user for given username."""
        raise NotImplementedError("Repository.get_user_by_username")

    def list_users(
            self,
            where_spec: Optional[WhereSpec] = None,
            order_spec: Optional[OrderSpec] = None) -> Iterator[User]:
        """
        Return an iterator of all or some users.

        If `where_spec` is not None, only the users according to
        a specification are returned. The keys of `where_spec` are composed of
        valid user attributes and a relation specification, separated by "__".
        Relation specifications are one of: "eq", "ne", "ge", "gt", "lt", and
        "le".  Examples are: "username__eq", "is_host__eq", "key__ne".

        if `order_spec` is not None, the result is sorted with respect to given
        keys. Keys are valid user attributes, optionally prefixed by "-" or
        "+".  If the prefix "-" is given, sorting is descending, else it is
        ascending. Examples: "username", "-username".
        """
        raise NotImplementedError("Repository.list_users")

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        raise NotImplementedError("Repository.set_grouping")

    def get_grouping(self, key: KeyType) -> Grouping:
        """Return grouping with given key."""
        raise NotImplementedError("Repository.get_grouping")

    def list_groupings(
            self,
            where_spec: Optional[WhereSpec] = None,
            order_spec: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """
        Return an iterator of all or some groupings.

        See method `list_users` for a detailed description of `where_spec`
        and `order_spec`.
        """
        raise NotImplementedError("Repository.list_groupings")


class RepositoryFactory:
    """An abstract factory for repositories."""

    def create(self):
        """Create and setup a repository."""
        raise NotImplementedError("RepositoryFactory.open")

    def close(self, repository: Repository):
        """Close the given repository."""
        raise NotImplementedError("RepositoryFactory.close")
