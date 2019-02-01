
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

import random
import uuid
from typing import Any, Iterator, Optional, TypeVar

from .base import (
    DuplicateKey, NothingToUpdate, OrderSpec, Repository, RepositoryFactory, WhereSpec)
from .models import UserGroup, UserRegistration
from .proxy import ProxyRepository
from ..models import Grouping, Groups, KeyType, Model, Registration, User


class RamRepositoryFactory(RepositoryFactory):
    """Maintain a singleton RAM-based repository."""

    def __init__(self, repository_url: str):
        """Initialize the factory."""
        super().__init__(repository_url)
        self._repository: Optional[RamRepository] = None

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        return True

    def create(self) -> Repository:
        """Create and setup a repository."""
        if not self._repository:
            self._repository = RamRepository()
        return ProxyRepository(self._repository)


class RamRepository(Repository):
    """RAM repository."""

    def __init__(self):
        """Initialize the repository."""
        self._users = {}
        self._users_ident = {}
        self._groupings = {}
        self._groupings_code = {}
        self._registrations = {}
        self._groups = {}
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
            if previous_user.ident != user.ident:
                del self._users_ident[previous_user.ident]
        else:
            user = user._replace(key=self._uuid())

        other_user = self._users_ident.get(user.ident)
        if other_user and user.key != other_user.key:
            raise DuplicateKey("User.ident", user.ident)
        self._users[user.key] = self._users_ident[user.ident] = user
        return user

    def get_user(self, key: KeyType) -> Optional[User]:
        """Return user with given key or None."""
        return self._users.get(key, None)

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user with given ident, or None."""
        return self._users_ident.get(ident, None)

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[User]:
        """Return an iterator of all or some users."""
        return process_where_order(self._users.values(), where, order)

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
        return process_where_order(self._groupings.values(), where, order)

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        registration.validate()
        self._registrations[(registration.grouping, registration.participant)] = \
            registration
        return registration

    def get_registration(self, grouping: KeyType, participant: KeyType) -> Registration:
        """Return registration with given grouping and participant."""
        return self._registrations.get((grouping, participant), None)

    def count_registrations_by_grouping(self, grouping: KeyType) -> int:
        """Return number of registration for given grouping."""
        return len([g for g, _ in self._registrations if g == grouping])

    def delete_registration(self, grouping: KeyType, participant: KeyType) -> None:
        """Delete the given registration from the repository."""
        try:
            del self._registrations[(grouping, participant)]
        except KeyError:
            pass

    def iter_groupings_by_participant(
            self,
            participant: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all groupings the participant applied to."""
        return process_where_order(
            (self.get_grouping(g) for g, p in self._registrations if p == participant),
            where,
            order)

    def iter_user_registrations_by_grouping(
            self,
            grouping: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserRegistration]:
        """Return an iterator of user data of some participants."""
        return process_where_order(
            (UserRegistration(self._users[p], r.preferences)
                for (g, p), r in self._registrations.items() if g == grouping),
            where,
            order)

    def set_groups(self, grouping: KeyType, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        self._groups[grouping] = groups

    def get_groups(self, grouping: KeyType) -> Groups:
        """Get groups builded for grouping."""
        return self._groups.get(grouping, ())

    def iter_groups_by_user(
            self,
            user: KeyType,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserGroup]:
        """Return an iterator of group data of some participants."""
        user_obj = self._users[user]
        print("UOBJ", user_obj)
        result = []
        for grouping, groups in self._groups.items():
            grouping_obj = self._groupings[grouping]
            for group in groups:
                print("GROU", group)
                if user_obj in group:
                    result.append(UserGroup(grouping, grouping_obj.name, group))
        return process_where_order(result, where, order)


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


ModelT = TypeVar('ModelT')


def process_where(
        result: Iterator[ModelT], where: Optional[WhereSpec]) -> Iterator[ModelT]:
    """Filter result according to specification."""
    if where:
        for where_spec, where_val in where.items():
            where_spec_split = where_spec.split("__")
            where_field = where_spec_split[0]
            where_relop = where_spec_split[1]
            pred = WherePredicate(where_field, where_relop, where_val).pred()
            result = iter([elem for elem in result if pred(elem)])
    return result


def process_order(
        result: Iterator[ModelT], order: Optional[OrderSpec]) -> Iterator[ModelT]:
    """Sort result with respect to order specifications."""
    list_result = list(result)
    if order:
        for order_field in reversed(order):
            if order_field.startswith("-"):
                reverse = True
                order_field = order_field[1:]
            else:
                reverse = False
                if order_field.startswith("+"):
                    order_field = order_field[1:]

            list_result.sort(
                key=lambda obj: getattr(
                    obj, order_field),  # pylint: disable=cell-var-from-loop
                reverse=reverse)
    else:
        random.shuffle(list_result)
    return iter(list_result)


def process_where_order(
        result: Iterator[ModelT],
        where: Optional[WhereSpec],
        order: Optional[OrderSpec]) -> Iterator[ModelT]:
    """Process the where and order specification."""
    result = process_where(result, where)
    result = process_order(result, order)
    return result
