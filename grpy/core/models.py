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

"""Data models."""

import dataclasses
import datetime
import enum
from typing import Dict, FrozenSet, Optional, Tuple
from uuid import UUID, uuid4

from .utils import now


class KeyType(UUID):
    """Base class for all key types."""

    def __init__(
            self,
            hex=None,  # pylint: disable=redefined-builtin
            bytes_le=None,
            int: Optional[int] = None,  # pylint: disable=redefined-builtin
            key=None):
        """Initialize the key type."""
        if key is not None:
            int = key.int
        elif hex is None and bytes_le is None and int is None:
            int = uuid4().int
        super().__init__(hex=hex, bytes_le=bytes_le, int=int)

    def __eq__(self, other) -> bool:
        """
        Compare key types.

        This is needed to make objects of different sub-classes distinct, even
        if they contain the same integer value.
        """
        if isinstance(other, type(self)):
            return self.int == other.int
        return False

    def __hash__(self) -> int:
        """Hash the key type.

        This is needed, because `__eq__` was re-implemented.
        """
        return hash(self.int)


class ValidationFailed(Exception):
    """Model validation failed."""


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class Model:
    """Base model for all model classes."""


class UserKey(KeyType):
    """Key to identify an user."""


class Permissions(enum.Flag):
    """User permissions."""

    INACTIVE = 1
    HOST = 2
    ADMIN = 4


@dataclasses.dataclass(frozen=True)
class User(Model):
    """User data."""

    key: Optional[UserKey]
    ident: str
    permissions: Permissions = Permissions(0)
    last_login: Optional[datetime.datetime] = None

    @property
    def is_active(self) -> bool:
        """Return True if user is an active user."""
        return not bool(self.permissions & Permissions.INACTIVE)

    @property
    def is_host(self) -> bool:
        """Return True if user is a host."""
        return bool(self.permissions & Permissions.HOST)

    @property
    def is_admin(self) -> bool:
        """Return True if user is an (user) administrator."""
        return bool(self.permissions & Permissions.ADMIN)

    def validate(self) -> None:
        """Check model for consistency."""
        if self.key and not isinstance(self.key, UserKey):
            raise ValidationFailed("Key is not an UserKey: " + repr(self.key))
        if not self.ident:
            raise ValidationFailed("Ident is empty: {}".format(self))


class GroupingState(enum.Enum):
    """
    State of a grouping.

    Since many states can only be detected by reading other data instances,
    `Grouping` does'nt provides an appropriate method for getting the state.
    The state must be recovered by other means.

    `UNKNOWN`: state of grouping cannot be determined.

    `NEW`: grouping is freshly created, only maintenance operations are allowed.

    `AVAILABLE`: user can register for grouping.

    `FINAL`: registration period is over, grouping process can be started.

    `GROUPED`: groups were formed, but nothing is fixed.

    `FASTENED`: formed groups cannot be changed any more.

    `CLOSED`: grouping is only visible to host; it can be deleted.
    """

    UNKNOWN = enum.auto()
    NEW = enum.auto()
    AVAILABLE = enum.auto()
    FINAL = enum.auto()
    GROUPED = enum.auto()
    FASTENED = enum.auto()
    CLOSED = enum.auto()


class GroupingKey(KeyType):
    """Key to identify a grouping."""


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class Grouping(Model):
    """Grouping data."""

    key: Optional[GroupingKey]
    code: str
    name: str
    host_key: UserKey
    begin_date: datetime.datetime
    final_date: datetime.datetime
    close_date: Optional[datetime.datetime]
    policy: str
    max_group_size: int
    member_reserve: int
    note: str

    def validate(self) -> None:
        """Check model for consistency."""
        if self.key and not isinstance(self.key, GroupingKey):
            raise ValidationFailed("Key is not a GroupingKey: " + repr(self.key))
        if not self.code:
            raise ValidationFailed("Code is empty: {}".format(self))
        if not self.name:
            raise ValidationFailed("Name is empty: {}".format(self))
        if not isinstance(self.host_key, UserKey):
            raise ValidationFailed("Host is not an UserKey: " + repr(self.host_key))
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
                "Maximum group size < 1: {}".format(self.max_group_size))
        if self.member_reserve < 0:
            raise ValidationFailed("Member reserve < 0: {}".format(self.member_reserve))

    def get_state(self) -> GroupingState:
        """
        Calculate grouping state.

        This can be done only partially. The states `GroupingState.FINAL` and
        `GroupingState.CLOSED` need further refinement.
        """
        yet = now()
        if yet < self.begin_date:
            return GroupingState.NEW
        if yet < self.final_date:
            return GroupingState.AVAILABLE
        if self.close_date is None or yet < self.close_date:
            return GroupingState.FINAL
        return GroupingState.CLOSED

    def can_register(self) -> bool:
        """Check that grouping process can start now."""
        return self.get_state() == GroupingState.AVAILABLE


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class UserPreferences:
    """Base class for user preferences for a given policy."""


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class Registration(Model):
    """Data for an registration for a grouping by a participant."""

    grouping_key: GroupingKey
    user_key: UserKey
    preferences: UserPreferences

    def validate(self) -> None:
        """Check model for consistency."""
        if not isinstance(self.grouping_key, GroupingKey):
            raise ValidationFailed(
                "Grouping is not a GroupingKey: " + repr(self.grouping_key))
        if not isinstance(self.user_key, UserKey):
            raise ValidationFailed(
                "Participant is not an UserKey: " + repr(self.user_key))
        if not isinstance(self.preferences, UserPreferences):
            raise ValidationFailed(
                "Preferences is not a UserPreferences: {}".format(self.preferences))


PolicyData = Dict[User, UserPreferences]
Group = FrozenSet[UserKey]
Groups = Tuple[Group, ...]
