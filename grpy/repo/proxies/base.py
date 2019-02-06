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

"""Base proxy repository."""


from typing import Iterator, Optional, Sequence

from ..base import Message, OrderSpec, Repository, WhereSpec
from ..models import UserGroup, UserRegistration
from ...models import (
    Grouping, GroupingKey, Groups, Registration, User, UserKey)


class BaseProxyRepository(Repository):
    """A repository that delegates all requests to another repository."""

    def __init__(self, delegate: Repository):
        """Initialize the proxy repository."""
        self._delegate = delegate

    def get_messages(self, delete: bool = False) -> Sequence[Message]:
        """Return all repository-related messages."""
        return self._delegate.get_messages(delete)

    def close(self, success: bool) -> None:
        """Close the repository, store all permanent data."""
        self._delegate.close(success)

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        return self._delegate.set_user(user)

    def get_user(self, user_key: UserKey) -> Optional[User]:
        """Return user for given primary key."""
        return self._delegate.get_user(user_key)

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user for given ident."""
        return self._delegate.get_user_by_ident(ident)

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[User]:
        """Return an iterator of all or some users."""
        return self._delegate.iter_users(where, order)

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        return self._delegate.set_grouping(grouping)

    def get_grouping(self, grouping_key: GroupingKey) -> Optional[Grouping]:
        """Return grouping with given key."""
        return self._delegate.get_grouping(grouping_key)

    def get_grouping_by_code(self, code: str) -> Optional[Grouping]:
        """Return grouping with given short code."""
        return self._delegate.get_grouping_by_code(code)

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all or some groupings."""
        return self._delegate.iter_groupings(where, order)

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        return self._delegate.set_registration(registration)

    def get_registration(
            self,
            grouping_key: GroupingKey, user_key: UserKey) -> Optional[Registration]:
        """Return registration with given grouping and user."""
        return self._delegate.get_registration(grouping_key, user_key)

    def count_registrations_by_grouping(self, grouping_key: GroupingKey) -> int:
        """Return number of registration for given grouping."""
        return self._delegate.count_registrations_by_grouping(grouping_key)

    def delete_registration(self, grouping_key: GroupingKey, user_key: UserKey) -> None:
        """Delete the given registration from the repository."""
        self._delegate.delete_registration(grouping_key, user_key)

    def iter_groupings_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        return self._delegate.iter_groupings_by_user(user_key, where, order)

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserRegistration]:
        """Return an iterator of user data of some user."""
        return self._delegate.iter_user_registrations_by_grouping(
            grouping_key, where, order)

    def set_groups(self, grouping_key: GroupingKey, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        return self._delegate.set_groups(grouping_key, groups)

    def get_groups(self, grouping_key: GroupingKey) -> Groups:
        """Get groups builded for grouping."""
        return self._delegate.get_groups(grouping_key)

    def iter_groups_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserGroup]:
        """Return an iterator of group data of some user."""
        return self._delegate.iter_groups_by_user(user_key, where, order)
