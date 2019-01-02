
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

"""In-memory repository, stored in RAM."""

import uuid
from typing import Iterator, Optional

from .base import (
    DuplicateKey, Grouping, KeyType, Order, Repository, RepositoryFactory,
    User, Where)


class RamRepositoryFactory(RepositoryFactory):
    """Maintain a singleton RAM-based repository."""

    def __init__(self):
        """Initialize the factory."""
        self._repository = None

    def create(self) -> Repository:
        """Create and setup a repository."""
        if not self._repository:
            self._repository = RamRepository()
        return self._repository

    def close(self, repository: Repository):
        """Close the given repository."""


class RamRepository(Repository):
    """RAM repository."""

    def __init__(self):
        """Initialize the repository."""
        self._users = {}
        self._users_username = {}
        self._groupings = {}

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        if user.key:
            if user.key not in self._users:
                raise ValueError("User with key {} not in repository".format(user.key))
        else:
            new_key = uuid.uuid4()
            user = user._replace(key=new_key)

        other_user = self._users_username.get(user.username)
        if other_user and user.key != other_user.key:
            raise DuplicateKey("User.username " + user.username)
        self._users[user.key] = self._users_username[user.username] = user
        return user

    def get_user(self, key: KeyType) -> Optional[User]:
        """Return user with given key or None."""
        return self._users.get(key, None)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Return user with given username, or None."""
        return self._users_username.get(username, None)

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        if grouping.key:
            if grouping.key in self._groupings:
                raise ValueError(
                    "Grouping with key {} not in repository".format(grouping.key))
        else:
            new_key = uuid.uuid4()
            grouping = grouping._replace(key=new_key)

        self._groupings[grouping.key] = grouping
        return grouping

    def get_grouping(self, key: KeyType) -> Grouping:
        """Return grouping with given key."""
        return self._groupings.get(key, None)

    @staticmethod
    def compare_leq(element, field_name, value):
        """Return True if field is less than value."""
        element_value = getattr(element, field_name)
        if element_value is None:
            return True
        return element_value <= value

    @staticmethod
    def process_where(result, where):
        """Filter result according to specification."""
        if not where:
            return result
        for where_spec, where_val in where.items():
            where_spec_split = where_spec.split("__")
            if len(where_spec_split) == 1:
                where_field = where_spec
                where_relop = "eq"
            else:
                where_field = where_spec_split[0]
                where_relop = where_spec_split[1]

            if where_relop == "eq":
                result = [
                    elem for elem in result if getattr(elem, where_field) == where_val]
            elif where_relop == "leq":
                result = [
                    elem for elem in result
                    if RamRepository.compare_leq(elem, where_field, where_val)]

        return result

    @staticmethod
    def process_order(result, order_spec):
        """Sort result with respect to order specifications."""
        if not order_spec:
            return result
        result = list(result)
        for order in order_spec:
            if order.startswith("-"):
                reverse = True
                order = order[1:]
            else:
                reverse = False
                if order.startswith("+"):
                    order = order[1:]

            result.sort(
                key=lambda obj: getattr(
                    obj, order),  # pylint: disable=cell-var-from-loop
                reverse=reverse)
        return result

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
        result = self._groupings.values()
        result = self.process_where(result, where)
        result = self.process_order(result, order)
        return result
