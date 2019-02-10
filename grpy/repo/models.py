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

"""Repository related data models."""

import dataclasses  # pylint: disable=wrong-import-order
from typing import FrozenSet

from ..models import GroupingKey, User, UserKey, UserPreferences


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class UserRegistration:
    """Data for grouping policies: user data, registration data."""

    user: User
    preferences: UserPreferences


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class NamedUser:
    """The identifying data of an user."""

    user_key: UserKey
    user_ident: str


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class UserGroup:
    """Group data for a given user."""

    grouping_key: GroupingKey
    grouping_name: str
    group: FrozenSet[NamedUser]
