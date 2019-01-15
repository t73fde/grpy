
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

from .base import (
    DuplicateKey, NothingToUpdate, OrderSpec, Repository, RepositoryFactory, WhereSpec)
from ..models import Application, Grouping, KeyType, Model, User


class RamRepositoryFactory(RepositoryFactory):
    """Maintain a singleton RAM-based repository."""

    def __init__(self, repository_url: str):
        """Initialize the factory."""
        self._repository = None
        self._url = repository_url

    @property
    def url(self) -> str:
        """Return the configured URL to access the data store."""
        return self._url

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        return True

    def create(self) -> Repository:
        """Create and setup a repository."""
        if not self._repository:
            self._repository = RamRepository()
        return RamRepositoryProxy(self._repository)


class RamRepositoryProxy:
    """A proxy to a repository that checks create/open and close calls."""

    def __init__(self, repository: Repository):
        """Set the repository delegate."""
        self.__delegate = repository

    def close(self):
        """Close the repository."""
        self.__delegate.close()
        self.__delegate = None

    def __getattr__(self, name: str):
        """Return value of attribute, if is_open."""
        return getattr(self.__delegate, name)

    def __eq__(self, other):
        """Return True if both proxies have the same delegate."""
        return self.__delegate == other.__delegate  # pylint: disable=protected-access


class RamRepository(Repository):
    """RAM repository."""

    def __init__(self):
        """Initialize the repository."""
        self._users = {}
        self._users_username = {}
        self._groupings = {}
        self._groupings_code = {}
        self._applications = {}
        self._next_key = 0x10000

    def close(self):
        """Close the repository: nothing to do here."""

    def _uuid(self) -> uuid.UUID:
        """Return a new UUID."""
        result = uuid.UUID(int=self._next_key)
        self._next_key += 1
        return result

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        user.validate()
        if user.key:
            try:
                previous_user = self._users[user.key]
            except KeyError:
                raise NothingToUpdate("Missing user", user.key)
            if previous_user.username != user.username:
                del self._users_username[previous_user.username]
        else:
            user = user._replace(key=self._uuid())

        other_user = self._users_username.get(user.username)
        if other_user and user.key != other_user.key:
            raise DuplicateKey("User.username", user.username)
        self._users[user.key] = self._users_username[user.username] = user
        return user

    def get_user(self, key: KeyType) -> Optional[User]:
        """Return user with given key or None."""
        return self._users.get(key, None)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Return user with given username, or None."""
        return self._users_username.get(username, None)

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[User]:
        """Return an iterator of all or some users."""
        result = self._users.values()
        result = process_where(result, where)
        result = process_order(result, order)
        return result

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        grouping.validate()
        if grouping.key:
            try:
                previous_grouping = self._groupings[grouping.key]
            except KeyError:
                raise NothingToUpdate("Missing grouping", grouping.key)
            if previous_grouping.code != grouping.code:
                del self._groupings_code[previous_grouping.code]
        else:
            grouping = grouping._replace(key=self._uuid())

        other_grouping = self._groupings_code.get(grouping.code)
        if other_grouping and grouping.key != other_grouping.key:
            raise DuplicateKey("Grouping.code", grouping.code)

        self._groupings[grouping.key] = self._groupings_code[grouping.code] = grouping
        return grouping

    def get_grouping(self, key: KeyType) -> Grouping:
        """Return grouping with given key."""
        return self._groupings.get(key, None)

    def get_grouping_by_code(self, code: str) -> Grouping:
        """Return grouping with given short code."""
        return self._groupings_code.get(code, None)

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all or some groupings."""
        result = self._groupings.values()
        result = process_where(result, where)
        result = process_order(result, order)
        return result

    def set_application(self, application: Application) -> Application:
        """Add / update a grouping application."""
        application.validate()
        self._applications[(application.grouping, application.participant)] = \
            application
        return application

    def get_application(self, grouping: KeyType, participant: KeyType) -> Application:
        """Return application with given grouping and participant."""
        return self._applications.get((grouping, participant), None)


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
    if where:
        for where_spec, where_val in where.items():
            where_spec_split = where_spec.split("__")
            where_field = where_spec_split[0]
            where_relop = where_spec_split[1]
            pred = WherePredicate(where_field, where_relop, where_val).pred()
            result = [elem for elem in result if pred(elem)]
    return result


def process_order(
        result: Iterator[Model], order: Optional[OrderSpec]) -> Iterator[Model]:
    """Sort result with respect to order specifications."""
    if not order:
        return result
    result = list(result)
    for order_field in reversed(order):
        if order_field.startswith("-"):
            reverse = True
            order_field = order_field[1:]
        else:
            reverse = False
            if order_field.startswith("+"):
                order_field = order_field[1:]

        result.sort(
            key=lambda obj: getattr(
                obj, order_field),  # pylint: disable=cell-var-from-loop
            reverse=reverse)
    return result
