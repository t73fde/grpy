##
#    Copyright (c) 2018,2019 Detlef Stern
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

import dataclasses  # pylint: disable=wrong-import-order
from typing import Dict, Iterable, Optional, Sequence, Tuple, cast

from ..models import (Grouping, GroupingKey, GroupingState, Groups,
                      Registration, User, UserKey)
from .base import (Connection, DuplicateKey, Message, NothingToUpdate,
                   OrderSpec, Repository, WhereSpec)
from .models import NamedUser, UserGroup, UserRegistration
from .proxies.algebra import AlgebraConnection


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
        self._next_key: int = 0x10000

    def next_int(self) -> int:
        """Return a new int to produce another KeyType object."""
        self._next_key += 1
        return self._next_key


class RamRepository(Repository):
    """Maintain a singleton RAM-based repository."""

    def __init__(self, repository_url: str):
        """Initialize the repository."""
        super().__init__(repository_url)
        self._repository: Optional[RamConnection] = None
        self._state: Optional[RamRepositoryState] = None

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        return True

    def initialize(self) -> bool:
        """Initialize the repository, if needed."""
        return True

    def create(self) -> Connection:
        """Create and setup a repository."""
        if not self._state:
            self._state = RamRepositoryState()
        return AlgebraConnection(RamConnection(self._state))


class RamConnection(Connection):  # pylint: disable=too-many-public-methods
    """RAM connection."""

    def __init__(self, state):
        """Initialize the repository."""
        self._state: RamRepositoryState = state

    def get_messages(self) -> Sequence[Message]:
        """Return all repository-related messages."""
        return []

    def has_errors(self) -> bool:
        """Return True if some errors were detected with this connection."""
        return False

    def close(self, _success: bool) -> None:
        """Close the repository: nothing to do here."""
        self._state = cast(RamRepositoryState, None)

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        if user.key:
            try:
                previous_user = self._state.users[user.key]
            except KeyError:
                raise NothingToUpdate("Missing user", user.key)
            if previous_user.ident != user.ident:
                del self._state.users_ident[previous_user.ident]
        else:
            user = dataclasses.replace(user, key=UserKey(int=self._state.next_int()))

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
            order: Optional[OrderSpec] = None) -> Iterable[User]:
        """Return an iterator of all or some users."""
        return self._state.users.values()

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        if grouping.key:
            try:
                previous_grouping = self._state.groupings[grouping.key]
            except KeyError:
                raise NothingToUpdate("Missing grouping", grouping.key)
            if previous_grouping.code != grouping.code:
                del self._state.groupings_code[previous_grouping.code]
        else:
            grouping = dataclasses.replace(
                grouping, key=GroupingKey(int=self._state.next_int()))

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

    def get_grouping_state(self, grouping_key: GroupingKey) -> GroupingState:
        """Return current state of given grouping."""
        grouping = self._state.groupings.get(grouping_key, None)
        if grouping is None:
            return GroupingState.UNKNOWN
        state = grouping.get_state()
        if state not in (GroupingState.FINAL, GroupingState.CLOSED):
            return state
        has_regs = any(g for g, _ in self._state.registrations if g == grouping_key)
        has_groups = bool(self._state.groups.get(grouping_key, False))
        if has_groups:
            if has_regs:
                return GroupingState.GROUPED
            if state == GroupingState.FINAL:
                return GroupingState.FASTENED
            return GroupingState.CLOSED
        return GroupingState.FINAL

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all or some groupings."""
        return self._state.groupings.values()

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
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

    def delete_registrations(self, grouping_key: GroupingKey) -> None:
        """Delete all registrations of a grouping from the repository."""
        keys = {
            (g_key, u_key)
            for g_key, u_key in self._state.registrations.keys()
            if g_key == grouping_key}
        for key in keys:
            del self._state.registrations[key]

    def iter_groupings_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        return (self._state.groupings[g] for g, p in self._state.registrations
                if p == user_key)

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserRegistration]:
        """Return an iterator of user data of some user."""
        return (UserRegistration(self._state.users[p], r.preferences)
                for (g, p), r in self._state.registrations.items()
                if g == grouping_key)

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
            order: Optional[OrderSpec] = None) -> Iterable[UserGroup]:
        """Return an iterator of group data of some user."""
        result = []
        for grouping, groups in self._state.groups.items():
            grouping_obj = self._state.groupings[grouping]
            for group in groups:
                if user_key in group:
                    named_group = frozenset(
                        NamedUser(g, self._state.users[g].ident) for g in group)
                    result.append(UserGroup(
                        grouping, grouping_obj.name, grouping_obj.close_date,
                        named_group))
        return result
