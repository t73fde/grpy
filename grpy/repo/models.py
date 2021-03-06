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

import dataclasses
import datetime
from typing import FrozenSet, Optional

from ..core.models import GroupingKey, User, UserKey, UserPreferences


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class UserRegistration:
    """Data for grouping policies: user data, registration data."""

    user: User
    preferences: UserPreferences


@dataclasses.dataclass(  # pylint: disable=too-few-public-methods
    order=True, frozen=True)
class NamedUser:
    """The identifying data of an user."""

    user_ident: str
    user_key: UserKey


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class UserGroup:
    """Group data for a given user."""

    grouping_key: GroupingKey
    grouping_name: str
    grouping_close_date: Optional[datetime.datetime]
    group: FrozenSet[NamedUser]
