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

"""Policies for group forming."""

import functools
import random
from typing import Callable, Dict, List, cast

from ..models import Groups, PolicyData, User, UserKey
from .preferred import preferred_policy
from .simple_belbin import simple_belbin_policy
from .sizes import group_sizes


def _build_groups(
        users: List[User], max_group_size: int, member_reserve: int) -> Groups:
    """Assign users to groups."""
    sizes = group_sizes(len(users), max_group_size, member_reserve)
    groups = []
    for size in sizes:
        groups.append(frozenset(cast(UserKey, user.key) for user in users[-size:]))
        users = users[:-size]
    return tuple(groups)


def identity_policy(
        data: PolicyData, max_group_size: int, member_reserve: int) -> Groups:
    """Build groups by name."""
    users = sorted((user for user in data), key=lambda u: u.ident, reverse=True)
    return _build_groups(users, max_group_size, member_reserve)


def random_policy(data: PolicyData, max_group_size: int, member_reserve: int) -> Groups:
    """Build groups randomly."""
    users = [user for user in data]
    random.shuffle(users)
    return _build_groups(users, max_group_size, member_reserve)


POLICY = Callable[[PolicyData, int, int], Groups]
POLICY_FUNCS: Dict[str, POLICY] = {
    'RD': random_policy,
    'ID': identity_policy,
    'P1': functools.partial(preferred_policy, 1),
    'P2': functools.partial(preferred_policy, 2),
    'P3': functools.partial(preferred_policy, 3),
    'SB': simple_belbin_policy,
}


def get_policy(code: str) -> POLICY:
    """Create a policy object based on code."""
    return POLICY_FUNCS.get(code, identity_policy)
