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

from typing import Callable, List, Optional, Sequence

from ...core.models import (Grouping, GroupingKey, Groups, Registration, User,
                            UserKey, ValidationFailed)
from ..base import Connection, DuplicateKey, Message, NothingToUpdate
from .base import BaseProxyConnection
from .filter import FilterProxyConnection


class ValidatingProxyConnection(BaseProxyConnection):
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


class CatchingProxyConnection(FilterProxyConnection):
    """A repository that catches all exceptions by the delegated repository."""

    def __init__(self, delegate: Connection):
        """Initialize the proxy repository."""
        super().__init__(delegate)
        self._messages: List[Message] = []
        self._has_errors = False

    def _add_message(
            self,
            category: str,
            text: str,
            exception: Optional[Exception] = None) -> None:
        """Add a message to the list of messages."""
        self._messages.append(
            Message(category=category, text=text, exception=exception))
        self._has_errors = True

    def _filter(self, function: Callable, default, *args):
        """Execute function call and catches all relevant exceptions."""
        try:
            return super()._filter(function, default, *args)
        except ValidationFailed as exc:
            self._add_message(
                "critical",
                "Internal validation failed: " + " ".join(str(arg) for arg in exc.args))
        except DuplicateKey as exc:
            if exc.args[0] in ("User.ident", "Grouping.code"):
                raise
            self._add_message(
                "critical",
                "Duplicate key for field '%s' with value '%s'" % (
                    exc.args[0], exc.args[1]),
                exc)
        except NothingToUpdate as exc:
            self._add_message(
                "critical", "%s: try to update key %s" % (exc.args[0], exc.args[1]))
        except Exception as exc:  # pylint: disable=broad-except
            exc_class = exc.__class__
            self._add_message(
                "critical",
                exc_class.__module__ + "." + exc_class.__name__ + ": " + str(exc),
                exc)

        return default

    def get_messages(self) -> Sequence[Message]:
        """Return all repository-related messages."""
        my_messages = list(self._messages)
        self._messages = []
        delegate_messages = super().get_messages()
        if delegate_messages:
            my_messages.extend(delegate_messages)
        return my_messages

    def has_errors(self) -> bool:
        """Return True if some errors were detected with this connection."""
        if self._has_errors:
            return True
        return super().has_errors()
