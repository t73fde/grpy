
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

"""Data models."""

import datetime
import enum
import uuid
from typing import Dict, FrozenSet, NamedTuple, Optional, Tuple

from .utils import now


KeyType = uuid.UUID


class ValidationFailed(Exception):
    """Model validation failed."""


class Permission(enum.Flag):
    """User permissions."""

    HOST = 2


class User(NamedTuple):
    """User data."""

    key: Optional[KeyType]
    ident: str
    permission: Permission = Permission(0)

    @property
    def is_host(self) -> bool:
        """Return True if user is a host."""
        return bool(self.permission & Permission.HOST)

    def validate(self) -> None:
        """Check model for consistency."""
        if self.key and not isinstance(self.key, uuid.UUID):
            raise ValidationFailed("Key is not a UUID: {}".format(self.key))
        if not self.ident:
            raise ValidationFailed("Ident is empty: {}".format(self))


class Grouping(NamedTuple):
    """Grouping data."""

    key: Optional[KeyType]
    code: str
    name: str
    host_key: KeyType  # -> User
    begin_date: datetime.datetime
    final_date: datetime.datetime
    close_date: Optional[datetime.datetime]
    policy: str
    max_group_size: int
    member_reserve: int
    note: str

    def validate(self) -> None:
        """Check model for consistency."""
        if self.key and not isinstance(self.key, uuid.UUID):
            raise ValidationFailed("Key is not a UUID: {}".format(self.key))
        if not self.code:
            raise ValidationFailed("Code is empty: {}".format(self))
        if not self.name:
            raise ValidationFailed("Name is empty: {}".format(self))
        if not isinstance(self.host_key, uuid.UUID):
            raise ValidationFailed("Host is not a UUID: {}".format(self.host_key))
        if self.begin_date >= self.final_date:
            raise ValidationFailed(
                "Begin date after final date: {} >= {}".format(
                    self.begin_date, self.final_date))
        if self.close_date and self.final_date >= self.close_date:
            raise ValidationFailed(
                "Final date after close date: {} >= {}".format(
                    self.final_date, self.close_date))
        if not self.policy:
            raise ValidationFailed("Policy is empty: {}".format(self))
        if self.max_group_size < 1:
            raise ValidationFailed(
                "Maximal group size < 1: {}".format(self.max_group_size))
        if self.member_reserve < 0:
            raise ValidationFailed("Member reserve < 0: {}".format(self.member_reserve))

    def is_registration_open(self) -> bool:
        """Check that registrations for given grouping are open."""
        return self.begin_date < now() < self.final_date

    def can_grouping_start(self) -> bool:
        """Check that grouping process can start now."""
        return self.final_date < now()


class UserPreferences(NamedTuple):
    """Base class for user preferences for a given policy."""


class Registration(NamedTuple):
    """Data for an registration for a grouping by a participant."""

    grouping_key: KeyType  # -> Grouping
    user_key: KeyType  # -> User
    preferences: UserPreferences

    def validate(self) -> None:
        """Check model for consistency."""
        if not isinstance(self.grouping_key, uuid.UUID):
            raise ValidationFailed(
                "Grouping is not a UUID: {}".format(self.grouping_key))
        if not isinstance(self.user_key, uuid.UUID):
            raise ValidationFailed(
                "Participant is not a UUID: {}".format(self.user_key))
        if not isinstance(self.preferences, UserPreferences):
            raise ValidationFailed(
                "Preferences is not a UserPreferences: {}".format(self.preferences))


PolicyData = Dict[User, UserPreferences]
Group = FrozenSet[KeyType]  # -> User
Groups = Tuple[Group, ...]
