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
from typing import Callable, List, Sequence

from .base import BaseProxyRepository
from .filter import FilterProxyRepository
from ..base import DuplicateKey, Message, NothingToUpdate, Repository
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


class CatchingProxyRepository(FilterProxyRepository):
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

    def _filter(self, function: Callable, default, *args):
        """Execute function call and catches all relevant exceptions."""
        try:
            return super()._filter(function, default, *args)
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
