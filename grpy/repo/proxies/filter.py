##
#    Copyright (c) 2019 Detlef Stern
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

"""Filter proxy connection."""

from datetime import datetime
from typing import Callable, Iterable, Optional, Sequence, cast

from ...core.models import (Grouping, GroupingKey, Groups, Registration, User,
                            UserKey, UserPreferences)
from ..base import Connection, Message, OrderSpec, WhereSpec
from ..models import UserGroup, UserRegistration
from .base import BaseProxyConnection


class FilterProxyConnection(  # pylint: disable=too-many-public-methods
        BaseProxyConnection):
    """A connection that delegates all requests to another connection."""

    def __init__(self, delegate: Connection):
        """Initialize the proxy connection."""
        super().__init__(delegate)
        self._user = User(UserKey(int=0), "*error*")
        self._grouping = Grouping(
            GroupingKey(int=0), "*code*", "*error*", UserKey(int=0),
            datetime(1970, 1, 1), datetime(1970, 1, 2), datetime(1970, 1, 3),
            "RD", 1, 0, "")
        self._registration = Registration(
            GroupingKey(int=0), UserKey(int=0), UserPreferences())

    def _filter(  # pylint: disable=no-self-use
            self, function: Callable, _default, *args):
        """Execute function call."""
        return function(*args)

    def get_messages(self) -> Sequence[Message]:
        """Return all connection-related messages."""
        return cast(Sequence[Message], self._filter(super().get_messages, ()))

    def has_errors(self) -> bool:
        """Return True if some errors were detected with this connection."""
        return cast(bool, self._filter(super().has_errors, True))

    def close(self, success: bool) -> None:
        """Close the connection, store all permanent data."""
        self._filter(super().close, None, success)

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        return cast(User, self._filter(super().set_user, self._user, user))

    def get_user(self, user_key: UserKey) -> Optional[User]:
        """Return user for given primary key."""
        return cast(Optional[User], self._filter(super().get_user, None, user_key))

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user for given ident."""
        return cast(Optional[User], self._filter(
            super().get_user_by_ident, None, ident))

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[User]:
        """Return an iterator of all or some users."""
        return cast(Iterable[User], self._filter(
            super().iter_users, (), where, order))

    def delete_user(self, user_key: UserKey) -> None:
        """Delete the user object referenced by the given key."""
        self._filter(super().delete_user, None, user_key)

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        return cast(Grouping, self._filter(
            super().set_grouping, self._grouping, grouping))

    def get_grouping(self, grouping_key: GroupingKey) -> Optional[Grouping]:
        """Return grouping with given key."""
        return cast(Optional[Grouping], self._filter(
            super().get_grouping, None, grouping_key))

    def get_grouping_by_code(self, code: str) -> Optional[Grouping]:
        """Return grouping with given short code."""
        return cast(Optional[Grouping], self._filter(
            super().get_grouping_by_code, None, code))

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all or some groupings."""
        return cast(Iterable[Grouping], self._filter(
            super().iter_groupings, (), where, order))

    def delete_grouping(self, grouping_key: GroupingKey) -> None:
        """Delete the grouping object referenced by the given key."""
        self._filter(super().delete_grouping, None, grouping_key)

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        return cast(Registration, self._filter(
            super().set_registration, self._registration, registration))

    def get_registration(
            self,
            grouping_key: GroupingKey, user_key: UserKey) -> Optional[Registration]:
        """Return registration with given grouping and user."""
        return cast(Optional[Registration], self._filter(
            super().get_registration, None, grouping_key, user_key))

    def count_registrations_by_grouping(self, grouping_key: GroupingKey) -> int:
        """Return number of registration for given grouping."""
        return cast(int, self._filter(
            super().count_registrations_by_grouping, 0, grouping_key))

    def delete_registration(self, grouping_key: GroupingKey, user_key: UserKey) -> None:
        """Delete the given registration from the repository."""
        self._filter(super().delete_registration, None, grouping_key, user_key)

    def delete_registrations(self, grouping_key: GroupingKey) -> None:
        """Delete all registrations of a grouping from the repository."""
        self._filter(super().delete_registrations, None, grouping_key)

    def iter_groupings_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        return cast(Iterable[Grouping], self._filter(
            super().iter_groupings_by_user, (), user_key, where, order))

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserRegistration]:
        """Return an iterator of user data of some user."""
        return cast(Iterable[UserRegistration], self._filter(
            super().iter_user_registrations_by_grouping, (),
            grouping_key, where, order))

    def set_groups(self, grouping_key: GroupingKey, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        self._filter(super().set_groups, None, grouping_key, groups)

    def get_groups(self, grouping_key: GroupingKey) -> Groups:
        """Get groups builded for grouping."""
        return cast(Groups, self._filter(super().get_groups, (), grouping_key))

    def iter_groups_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserGroup]:
        """Return an iterator of group data of some user."""
        return cast(Iterable[UserGroup], self._filter(
            super().iter_groups_by_user, (), user_key, where, order))
