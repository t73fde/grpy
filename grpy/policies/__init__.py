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

import dataclasses  # pylint: disable=wrong-import-order
import functools
import random
from typing import Callable, Dict, List, Set, Tuple, cast

from .genetic import Genome, Rating, StopStrategy, generic_genetic_policy
from .sizes import group_sizes
from ..models import Groups, PolicyData, User, UserKey, UserPreferences


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


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class PreferredPreferences(UserPreferences):
    """Perference for preferred users."""

    preferred: List[str]


PreferredData = Dict[UserKey, Set[UserKey]]


def build_preferred_rating_data(data: PolicyData, max_preferred: int) -> PreferredData:
    """Build data structure to help `preferred_rating_func."""
    max_preferred = max(0, max_preferred)
    ident_dict = {user.ident: cast(UserKey, user.key) for user in data}
    result = {}
    for user, preferences in data.items():
        key = cast(UserKey, user.key)
        if isinstance(preferences, PreferredPreferences):
            result[key] = {
                ident_dict[key] for key in preferences.preferred[:max_preferred]
                if key in ident_dict}
        else:
            result[key] = set()
    return result


def preferred_rating_func(genome: Genome, data: PreferredData) -> Rating:
    """Calculate a rating based on preferred users."""
    rating = 0.0
    for group in genome:
        group_set = set(group)
        for member in group:
            missing = data[member] - group_set
            rating += len(missing) ** 2.0
    return rating


def preferred_policy(
        max_preferred: int, data: PolicyData,
        max_group_size: int, member_reserve: int) -> Groups:
    """Build groups based on preferred users."""
    users = [cast(UserKey, user.key) for user in data]
    sizes = group_sizes(len(users), max_group_size, member_reserve)
    rating_data = build_preferred_rating_data(data, max_preferred)
    stop_strategy = StopStrategy(1000000, 500, 50, 0.5)
    result = generic_genetic_policy(
        users, sizes, preferred_rating_func, rating_data, stop_strategy)
    return result


STRONGLY_DISAGREE = 0
DISAGREE = 1
AGREE = 2
STRONGLY_AGREE = 3


SimpleBelbinAnswer = Tuple[int, int, int, int, int, int, int, int]
SIMPLE_BELBIN_ANSWER_COUNT = 8
DEFAULT_SIMPLE_BELBIN_ANSWER: SimpleBelbinAnswer = cast(
    SimpleBelbinAnswer, (STRONGLY_DISAGREE,) * SIMPLE_BELBIN_ANSWER_COUNT)


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class SimpleBelbinPreferences(UserPreferences):
    """Preference for simple belbin test."""

    answers: SimpleBelbinAnswer


SimpleBelbinData = Dict[UserKey, SimpleBelbinAnswer]


def build_simple_belbin_rating_data(data: PolicyData) -> SimpleBelbinData:
    """Build data structure to help `simple_belbin_rating_func."""
    result = {}
    for user, preferences in data.items():
        key = cast(UserKey, user.key)
        if isinstance(preferences, SimpleBelbinPreferences):
            if len(preferences.answers) == SIMPLE_BELBIN_ANSWER_COUNT:
                result[key] = preferences.answers
    return result


def simple_belbin_rating_func(genome: Genome, data: SimpleBelbinData) -> Rating:
    """Calculate a rating based on preferred users."""
    rating = 0.0
    for group in genome:
        group_answers = DEFAULT_SIMPLE_BELBIN_ANSWER
        for member in group:
            try:
                group_answers = cast(
                    SimpleBelbinAnswer,
                    tuple(max(a, b) for a, b in zip(group_answers, data[member])))
            except KeyError:
                pass
        rating += sum((STRONGLY_AGREE - answer) ** 2 for answer in group_answers)
    return rating


def simple_belbin_policy(
        data: PolicyData, max_group_size: int, member_reserve: int) -> Groups:
    """Build groups based on preferred users."""
    users = [cast(UserKey, user.key) for user in data]
    sizes = group_sizes(len(users), max_group_size, member_reserve)
    rating_data = build_simple_belbin_rating_data(data)
    stop_strategy = StopStrategy(1000000, 500, 50, 0.5)
    result = generic_genetic_policy(
        users, sizes, simple_belbin_rating_func, rating_data, stop_strategy)
    return result


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
