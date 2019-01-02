
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
from typing import Any, Iterator, Optional

from .base import DuplicateKey, OrderSpec, Repository, RepositoryFactory, WhereSpec
from ..models import Grouping, KeyType, Model, User


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

    def list_users(
            self,
            where_spec: Optional[WhereSpec] = None,
            order_spec: Optional[OrderSpec] = None) -> Iterator[User]:
        """Return an iterator of all or some users."""
        result = self._users.values()
        result = process_where(result, where_spec)
        result = process_order(result, order_spec)
        return result

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

    def list_groupings(
            self,
            where_spec: Optional[WhereSpec] = None,
            order_spec: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all or some groupings."""
        result = self._groupings.values()
        result = process_where(result, where_spec)
        result = process_order(result, order_spec)
        return result


class WherePredicate:
    """Filter attributes."""

    def __init__(self, field_name: str, where_op: str, filter_value: Any):
        """Initialize the filter."""
        self.name = field_name
        self.relop = where_op
        self.value = filter_value

    def pred(self):
        """Return the appropriate filter predicate."""
        return getattr(self, self.relop + "_pred")

    def eq_pred(self, data: Model) -> bool:
        """Return True if data[self.name] == self.value."""
        return getattr(data, self.name) == self.value

    def ne_pred(self, data: Model) -> bool:
        """Return True if data[self.name] != self.value."""
        return getattr(data, self.name) != self.value

    def lt_pred(self, data: Model) -> bool:
        """Return True if data[self.name] < self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return data_value < self.value

    def le_pred(self, data: Model) -> bool:
        """Return True if data[self.name] <= self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return data_value <= self.value

    def ge_pred(self, data: Model) -> bool:
        """Return True if data[self.name] >= self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return data_value >= self.value

    def gt_pred(self, data: Model) -> bool:
        """Return True if data[self.name] > self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return data_value > self.value


def process_where(
        result: Iterator[Model], where: Optional[WhereSpec]) -> Iterator[Model]:
    """Filter result according to specification."""
    if not where:
        return result
    for where_spec, where_val in where.items():
        where_spec_split = where_spec.split("__")
        where_field = where_spec_split[0]
        where_relop = where_spec_split[1]
        pred = WherePredicate(where_field, where_relop, where_val).pred()
        result = [elem for elem in result if pred(elem)]
    return result


def process_order(
        result: Iterator[Model], order_spec: Optional[OrderSpec]) -> Iterator[Model]:
    """Sort result with respect to order specifications."""
    if not order_spec:
        return result
    result = list(result)
    for order in reversed(order_spec):
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
