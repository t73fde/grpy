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

"""Business logic."""

import hashlib
import os
from typing import AbstractSet, List

from .models import Grouping, Groups, UserKey


def make_code(grouping: Grouping, unique: bool = False) -> str:
    """Build a short code for accessing a grouping."""
    sha = hashlib.sha256()
    values = (
        grouping.name,
        str(grouping.begin_date.date()),
        str(grouping.final_date.date()),
        grouping.policy,
    )
    for value in values:
        sha.update(value.encode('utf-8'))
    if unique:
        sha.update(os.urandom(8))
    num_value = int(sha.hexdigest(), 16)

    encoding = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    result: List[str] = []
    while len(result) < 6:
        num_value, rem = divmod(num_value, len(encoding))
        result.append(encoding[rem])
    return ''.join(result)


def remove_from_groups(groups: Groups, user_keys: AbstractSet[UserKey]) -> Groups:
    """Remove an user from the builded groups."""
    user_key_set = set(user_keys)
    group_list = []
    for group in groups:
        both = group.intersection(user_key_set)
        if both:
            new_group = group - both
            if new_group:
                group_list.append(new_group)
            user_key_set.difference_update(both)
        else:
            group_list.append(group)
    return tuple(group_list)
