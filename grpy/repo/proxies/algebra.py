##
#    Copyright (c) 2019-2021 Detlef Stern
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

"""Proxy connection that implements WHERE and ORDER."""

import random
from typing import Any, Callable, Iterable, Optional, Tuple, TypeVar, cast

from ...core.models import Grouping, GroupingKey, Model, User, UserKey
from ..base import OrderSpec, WhereSpec
from ..models import UserGroup, UserRegistration
from .base import BaseProxyConnection


class AlgebraConnection(BaseProxyConnection):
    """Connection that implements WHERE and ORDER for iter methods."""

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[User]:
        """Return an iterator of all or some users."""
        return process_where_order(super().iter_users(where, order), where, order)

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all or some groupings."""
        return process_where_order(super().iter_groupings(where, order), where, order)

    def iter_groupings_by_user(
            self, user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        return process_where_order(
            super().iter_groupings_by_user(user_key, where, order), where, order)

    def iter_user_registrations_by_grouping(
            self, grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserRegistration]:
        """Return an iterator of user data of some user."""
        return process_where_order(
            super().iter_user_registrations_by_grouping(grouping_key, where, order),
            where, order)

    def iter_groups_by_user(
            self, user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserGroup]:
        """Return an iterator of group data of some user."""
        return process_where_order(
            super().iter_groups_by_user(user_key, where, order), where, order)


ModelT = TypeVar('ModelT')
Predicate = Callable[[ModelT], bool]


class WherePredicate:
    """Filter attributes."""

    def __init__(self, field_name: str, where_op: str, filter_value: Any):
        """Initialize the filter."""
        self.name = field_name
        self.relop = where_op
        self.value = filter_value

    def pred(self) -> Predicate:
        """Return the appropriate filter predicate."""
        return cast(Predicate, getattr(self, self.relop + "_pred"))

    def eq_pred(self, data: Model) -> bool:
        """Return True if data[self.name] == self.value."""
        return cast(bool, getattr(data, self.name) == self.value)

    def ne_pred(self, data: Model) -> bool:
        """Return True if data[self.name] != self.value."""
        return cast(bool, getattr(data, self.name) != self.value)

    def lt_pred(self, data: Model) -> bool:
        """Return True if data[self.name] < self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return cast(bool, data_value < self.value)

    def le_pred(self, data: Model) -> bool:
        """Return True if data[self.name] <= self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return cast(bool, data_value <= self.value)

    def ge_pred(self, data: Model) -> bool:
        """Return True if data[self.name] >= self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return cast(bool, data_value >= self.value)

    def gt_pred(self, data: Model) -> bool:
        """Return True if data[self.name] > self.value."""
        data_value = getattr(data, self.name)
        if data_value is None:
            return True
        return cast(bool, data_value > self.value)


def process_where(
        result: Iterable[ModelT], where: Optional[WhereSpec]) -> Iterable[ModelT]:
    """Filter result according to specification."""
    if where:
        for where_spec, where_val in where.items():
            where_spec_split = where_spec.split("__")
            where_field = where_spec_split[0]
            where_relop = where_spec_split[1]
            pred = WherePredicate(where_field, where_relop, where_val).pred()
            result = [elem for elem in result if pred(elem)]
    return result


def _value_to_sort(obj: Any, name: str) -> Tuple[bool, Any]:
    """Produce a value that can be sorted even if value is None."""
    value = getattr(obj, name)
    if value is None:
        return (False, None)
    return (True, value)


def process_order(
        result: Iterable[ModelT], order: Optional[OrderSpec]) -> Iterable[ModelT]:
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
                key=lambda obj: _value_to_sort(
                    obj, order_field),  # pylint: disable=cell-var-from-loop
                reverse=reverse)
    else:
        random.shuffle(list_result)
    return list_result


def process_where_order(
        result: Iterable[ModelT],
        where: Optional[WhereSpec],
        order: Optional[OrderSpec]) -> Iterable[ModelT]:
    """Process the where and order specification."""
    result = process_where(result, where)
    result = process_order(result, order)
    return result
