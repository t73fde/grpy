
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
import uuid
from typing import NamedTuple, Optional


Model = NamedTuple
KeyType = uuid.UUID


class User(NamedTuple):
    """User data."""

    key: Optional[KeyType]
    username: str
    is_host: bool


class Grouping(NamedTuple):
    """Grouping data."""

    key: Optional[KeyType]
    name: str
    host: KeyType  # -> User
    begin_date: datetime.datetime
    final_date: datetime.datetime
    close_date: Optional[datetime.datetime]
    strategy: str
    max_group_size: int
    member_reserve: int
    note: str
