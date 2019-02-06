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

"""Checking proxy repositories."""

from datetime import datetime
from typing import Callable, Iterator, List, Optional, Sequence, cast

from .base import BaseProxyRepository
from ..base import (
    DuplicateKey, Message, NothingToUpdate, OrderSpec, Repository,
    UserGroup, UserRegistration, WhereSpec)
from ...models import (
    Grouping, GroupingKey, Groups, Registration, User, UserKey,
    UserPreferences, ValidationFailed)


class ValidatingProxyRepository(BaseProxyRepository):
    """A repository that validates input data before delegating calls."""

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        user.validate()
        return super().set_user(user)

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        grouping.validate()
        return super().set_grouping(grouping)

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        registration.validate()
        return super().set_registration(registration)

    def set_groups(self, grouping_key: GroupingKey, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        for group in groups:
            for member in group:
                if not isinstance(member, UserKey):
                    raise ValidationFailed(
                        "Group member is not an UserKey: " + repr(member))
        return super().set_groups(grouping_key, groups)


class CatchingProxyRepository(BaseProxyRepository):
    """A repository that catches all exceptions by the delegated repository."""

    def __init__(self, delegate: Repository):
        """Initialize the proxy repository."""
        super().__init__(delegate)
        self._user = User(UserKey(int=0), "*error*")
        self._grouping = Grouping(
            GroupingKey(int=0), "*code*", "*error*", UserKey(int=0),
            datetime(1970, 1, 1), datetime(1970, 1, 2), datetime(1970, 1, 3),
            "RD", 1, 0, "")
        self._registration = Registration(
            GroupingKey(int=0), UserKey(int=0), UserPreferences())
        self._messages: List[Message] = []

    def _try_catch(self, function: Callable, default, *args):
        """Execute function call and catches all relevant exceptions."""
        try:
            return function(*args)
        except ValidationFailed as exc:
            category = "critical"
            text = "Internal validation failed: " + \
                " ".join(str(arg) for arg in exc.args)
        except DuplicateKey as exc:
            if exc.args[0] == "Grouping.code":
                raise
            category = "critical"
            text = "Duplicate key for field '%s' with value '%s'" % (
                exc.args[0], exc.args[1])
        except NothingToUpdate as exc:
            category = "critical"
            text = "%s: try to update key %s" % (exc.args[0], exc.args[1])
        except Exception as exc:  # pylint: disable=broad-except
            category = "critical"
            exc_class = exc.__class__
            text = "Critical error: " + exc_class.__module__ + "." + \
                exc_class.__name__ + ": " + str(exc)

        self._messages.append(Message(category=category, text=text))
        return default

    def get_messages(self, delete: bool = False) -> Sequence[Message]:
        """Return all repository-related messages."""
        delegate_messages = super().get_messages(delete)
        my_messages = self._messages
        if delete:
            self._messages = []
        if delegate_messages:
            return my_messages + list(delegate_messages)
        return my_messages

    def close(self, success: bool) -> None:
        """Close the repository, store all permanent data."""
        self._try_catch(super().close, None, success)

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        return cast(User, self._try_catch(super().set_user, self._user, user))

    def get_user(self, user_key: UserKey) -> Optional[User]:
        """Return user for given primary key."""
        return cast(Optional[User], self._try_catch(super().get_user, None, user_key))

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user for given ident."""
        return cast(Optional[User], self._try_catch(
            super().get_user_by_ident, None, ident))

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[User]:
        """Return an iterator of all or some users."""
        return cast(Iterator[User], self._try_catch(
            super().iter_users, iter([]), where, order))

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        return cast(Grouping, self._try_catch(
            super().set_grouping, self._user, grouping))

    def get_grouping(self, grouping_key: GroupingKey) -> Optional[Grouping]:
        """Return grouping with given key."""
        return cast(Optional[Grouping], self._try_catch(
            super().get_grouping, None, grouping_key))

    def get_grouping_by_code(self, code: str) -> Optional[Grouping]:
        """Return grouping with given short code."""
        return cast(Optional[Grouping], self._try_catch(
            super().get_grouping_by_code, None, code))

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all or some groupings."""
        return cast(Iterator[Grouping], self._try_catch(
            super().iter_groupings, iter([]), where, order))

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        return cast(Registration, self._try_catch(
            super().set_registration, self._registration, registration))

    def get_registration(
            self,
            grouping_key: GroupingKey, user_key: UserKey) -> Optional[Registration]:
        """Return registration with given grouping and user."""
        return cast(Optional[Registration], self._try_catch(
            super().get_registration, None, grouping_key, user_key))

    def count_registrations_by_grouping(self, grouping_key: GroupingKey) -> int:
        """Return number of registration for given grouping."""
        return cast(int, self._try_catch(
            super().count_registrations_by_grouping, 0, grouping_key))

    def delete_registration(self, grouping_key: GroupingKey, user_key: UserKey) -> None:
        """Delete the given registration from the repository."""
        self._try_catch(super().delete_registration, None, grouping_key, user_key)

    def iter_groupings_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        return cast(Iterator[Grouping], self._try_catch(
            super().iter_groupings_by_user, iter([]), user_key, where, order))

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserRegistration]:
        """Return an iterator of user data of some user."""
        return cast(Iterator[UserRegistration], self._try_catch(
            super().iter_user_registrations_by_grouping, iter([]),
            grouping_key, where, order))

    def set_groups(self, grouping_key: GroupingKey, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        self._try_catch(super().set_groups, None, grouping_key, groups)

    def get_groups(self, grouping_key: GroupingKey) -> Groups:
        """Get groups builded for grouping."""
        return cast(Groups, self._try_catch(super().get_groups, (), grouping_key))

    def iter_groups_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterator[UserGroup]:
        """Return an iterator of group data of some user."""
        return cast(Iterator[UserGroup], self._try_catch(
            super().iter_groups_by_user, iter([]), user_key, where, order))
