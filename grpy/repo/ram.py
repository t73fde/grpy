
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
from typing import Any, Dict, Iterator, Optional, Tuple, TypeVar, cast

from .base import (
    DuplicateKey, NothingToUpdate, OrderSpec, Repository, RepositoryFactory, WhereSpec)
from .models import NamedUser, UserGroup, UserRegistration
from ..models import (
    Grouping, GroupingKey, Groups, NamedTuple, Registration, User, UserKey)


class RamRepositoryState:  # pylint: disable=too-few-public-methods
    """The actual data stored for a RamRepository."""

    def __init__(self):
        """Initialize the repository."""
        self.users: Dict[UserKey, User] = {}
        self.users_ident: Dict[str, User] = {}
        self.groupings: Dict[GroupingKey, Grouping] = {}
        self.groupings_code: Dict[str, Grouping] = {}
        self.registrations: Dict[Tuple[GroupingKey, UserKey], Registration] = {}
        self.groups: Dict[GroupingKey, Groups] = {}
        self._next_key = 0x10000

    def next_uuid(self) -> uuid.UUID:
        """Return a new UUID."""
        result = uuid.UUID(int=self._next_key)
        self._next_key += 1
        return result


class RamRepositoryFactory(RepositoryFactory):
    """Maintain a singleton RAM-based repository."""

    def __init__(self, repository_url: str):
        """Initialize the factory."""
        super().__init__(repository_url)
        self._repository: Optional[RamRepository] = None
        self._state: Optional[RamRepositoryState] = None

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        return True

    def initialize(self) -> bool:
        """Initialize the repository, if needed."""
        return True

    def create(self) -> Repository:
        """Create and setup a repository."""
        if not self._state:
            self._state = RamRepositoryState()
        return RamRepository(self._state)


class RamRepository(Repository):
    """RAM repository."""

    def __init__(self, state):
        """Initialize the repository."""
        self._state: RamRepositoryState = state

    def close(self):
        """Close the repository: nothing to do here."""
        self._state = None

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        user.validate()
        if user.key:
            try:
                previous_user = self._state.users[user.key]
            except KeyError:
                raise NothingToUpdate("Missing user", user.key)
            if previous_user.ident != user.ident:
                del self._state.users_ident[previous_user.ident]
        else:
            user = user._replace(key=cast(UserKey, self._state.next_uuid()))

        other_user = self._state.users_ident.get(user.ident)
        if other_user and user.key != other_user.key:
            raise DuplicateKey("User.ident", user.ident)
        self._state.users[cast(UserKey, user.key)] = \
            self._state.users_ident[user.ident] = user
        return user

    def get_user(self, user_key: UserKey) -> Optional[User]:
        """Return user with given key or None."""
        return self._state.users.get(user_key, None)

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user with given ident, or None."""
        return self._state.users_ident.get(ident, None)

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[User]:
        """Return an iterator of all or some users."""
        return process_where_order(iter(self._state.users.values()), where, order)

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        grouping.validate()
        if grouping.key:
            try:
                previous_grouping = self._state.groupings[grouping.key]
            except KeyError:
                raise NothingToUpdate("Missing grouping", grouping.key)
            if previous_grouping.code != grouping.code:
                del self._state.groupings_code[previous_grouping.code]
        else:
            grouping = grouping._replace(key=cast(GroupingKey, self._state.next_uuid()))

        other_grouping = self._state.groupings_code.get(grouping.code)
        if other_grouping and grouping.key != other_grouping.key:
            raise DuplicateKey("Grouping.code", grouping.code)

        self._state.groupings[cast(GroupingKey, grouping.key)] = \
            self._state.groupings_code[grouping.code] = grouping
        return grouping

    def get_grouping(self, grouping_key: GroupingKey) -> Optional[Grouping]:
        """Return grouping with given key."""
        return self._state.groupings.get(grouping_key, None)

    def get_grouping_by_code(self, code: str) -> Optional[Grouping]:
        """Return grouping with given short code."""
        return self._state.groupings_code.get(code, None)

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all or some groupings."""
        return process_where_order(iter(self._state.groupings.values()), where, order)

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        registration.validate()
        self._state.registrations[
            (registration.grouping_key, registration.user_key)] = registration
        return registration

    def get_registration(
            self,
            grouping_key: GroupingKey, user_key: UserKey) -> Optional[Registration]:
        """Return registration with given grouping and user."""
        return self._state.registrations.get((grouping_key, user_key), None)

    def count_registrations_by_grouping(self, grouping_key: GroupingKey) -> int:
        """Return number of registration for given grouping."""
        return len([g for g, _ in self._state.registrations if g == grouping_key])

    def delete_registration(self, grouping_key: GroupingKey, user_key: UserKey) -> None:
        """Delete the given registration from the repository."""
        try:
            del self._state.registrations[(grouping_key, user_key)]
        except KeyError:
            pass

    def iter_groupings_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        return process_where_order(
            (self._state.groupings[g] for g, p in self._state.registrations
                if p == user_key),
            where,
            order)

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserRegistration]:
        """Return an iterator of user data of some user."""
        return process_where_order(
            (UserRegistration(self._state.users[p], r.preferences)
                for (g, p), r in self._state.registrations.items()
                if g == grouping_key),
            where,
            order)

    def set_groups(self, grouping_key: GroupingKey, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        self._state.groups[grouping_key] = groups

    def get_groups(self, grouping_key: GroupingKey) -> Groups:
        """Get groups builded for grouping."""
        return cast(Groups, self._state.groups.get(grouping_key, ()))

    def iter_groups_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserGroup]:
        """Return an iterator of group data of some user."""
        result = []
        for grouping, groups in self._state.groups.items():
            grouping_obj = self._state.groupings[grouping]
            for group in groups:
                if user_key in group:
                    named_group = frozenset(
                        NamedUser(g, self._state.users[g].ident) for g in group)
                    result.append(UserGroup(grouping, grouping_obj.name, named_group))
        return process_where_order(iter(result), where, order)


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

    def eq_pred(self, data: NamedTuple) -> bool:
        """Return True if data[self.name] == self.value."""
        return cast(bool, getattr(data, self.name) == self.value)

    def ne_pred(self, data: NamedTuple) -> bool:
        """Return True if data[self.name] != self.value."""
        return cast(bool, getattr(data, self.name) != self.value)

    def lt_pred(self, data: NamedTuple) -> bool:
        """Return True if data[self.name] < self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return cast(bool, data_value < self.value)

    def le_pred(self, data: NamedTuple) -> bool:
        """Return True if data[self.name] <= self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return cast(bool, data_value <= self.value)

    def ge_pred(self, data: NamedTuple) -> bool:
        """Return True if data[self.name] >= self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return cast(bool, data_value >= self.value)

    def gt_pred(self, data: NamedTuple) -> bool:
        """Return True if data[self.name] > self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return cast(bool, data_value > self.value)


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
