
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


Where = Dict[str, Any]
Order = Sequence[str]


class DuplicateKey(Exception):
    """Signal that a key is not unique."""


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

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        raise NotImplementedError("Repository.set_grouping")

    def get_grouping(self, key: KeyType) -> Grouping:
        """Return grouping with given key."""
        raise NotImplementedError("Repository.get_grouping")

    def list_groupings(
            self,
            where: Optional[Where] = None,
            order: Optional[Order] = None) -> Iterator[Grouping]:
        """
        Return an iterator of all or some groupings.

        If `where` is not None, only the groupings according to a filter
        specification are returned. Valid keys are:

        * "host__eq": return only grouping of a given host user key.
        * "close_date__eq": return only grouping with the given close date.

        If `order` is given, the groupings are sorted with respect to
        a sequence of order specifications. If the first character of an order
        specification is a `-`-sign, the order is descending; if it is the
        `+`-sign (or the `+`-sign is missing), the order is ascending. Valid
        order specifications are:

        * "final_date": order by final date of the groupings.
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
