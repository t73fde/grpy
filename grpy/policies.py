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

import random
from typing import Callable, List, Sequence, Tuple, cast

from .models import Groups, PolicyData, UserKey


def group_sizes(
        num_participants: int,
        max_group_size: int, member_reserve: int) -> Sequence[int]:
    """Return a vector of group sizes."""
    if num_participants < 0:
        raise ValueError("num_participants < 0: %d" % num_participants)
    if member_reserve < 0:
        raise ValueError("member_reserve < 0: %d" % member_reserve)
    potential_participants = num_participants + member_reserve
    if potential_participants <= 0:
        return []
    if max_group_size <= 0:
        raise ValueError("max_group_size <= 0: %d" % max_group_size)

    empty_groups = 0
    while member_reserve > max_group_size + 1:
        empty_groups += 1
        member_reserve -= max_group_size
        potential_participants -= max_group_size

    num_groups, remainder = divmod(potential_participants, max_group_size)
    if remainder > 0:
        num_groups += 1

    avg_group_size, remainder = divmod(num_participants, num_groups)
    groups = [avg_group_size + 1] * remainder + \
             [avg_group_size] * (num_groups - remainder)
    return groups + [0] * empty_groups


def no_policy(data: PolicyData, max_group_size: int, member_reserve: int) -> Groups:
    """Build groups by name."""
    users = sorted((user for user in data), key=lambda u: u.ident, reverse=True)
    sizes = group_sizes(len(users), max_group_size, member_reserve)
    groups = []
    for size in sizes:
        groups.append(frozenset(cast(UserKey, user.key) for user in users[-size:]))
        users = users[:-size]
    return tuple(groups)


def random_policy(data: PolicyData, max_group_size: int, member_reserve: int) -> Groups:
    """Build groups randomly."""
    users = [user for user in data]
    random.shuffle(users)
    sizes = group_sizes(len(users), max_group_size, member_reserve)
    groups = []
    for size in sizes:
        groups.append(frozenset(cast(UserKey, user.key) for user in users[-size:]))
        users = users[:-size]
    return tuple(groups)


POLICY = Callable[[PolicyData, int, int], Groups]
POLICIES: Tuple[Tuple[str, str, POLICY], ...] = (
    ('RD', "Random", random_policy),
)
POLICY_META = [(code, name) for (code, name, _) in POLICIES]
POLICY_NAMES = dict(POLICY_META)
POLICY_FUNCS = {code: func for (code, _, func) in POLICIES}


def get_policy_names() -> List[Tuple[str, str]]:
    """Return list of policies."""
    return list(POLICY_META)


def get_policy_name(code: str) -> str:
    """Return policy name for given code."""
    return POLICY_NAMES.get(code, "")


def get_policy(code: str) -> POLICY:
    """Create a policy object based on code."""
    return POLICY_FUNCS.get(code, no_policy)
