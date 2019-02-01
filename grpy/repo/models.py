
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

"""Repository related data models."""

from typing import FrozenSet, NamedTuple

from ..models import KeyType, User, UserPreferences


class UserRegistration(NamedTuple):
    """Data for grouping policies: user data, registration data."""

    user: User
    preferences: UserPreferences


class NamedUser(NamedTuple):
    """The identifying data of an user."""

    user_key: KeyType  # -> models.User
    user_ident: str


class UserGroup(NamedTuple):
    """Group data for a given user."""

    grouping_key: KeyType  # -> models.Grouping
    grouping_name: str
    group: FrozenSet[NamedUser]
