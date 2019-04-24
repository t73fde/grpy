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

"""Policy for group forming by a simple belbin test."""

import dataclasses
from typing import Dict, Tuple, cast

from ..models import Groups, PolicyData, UserKey, UserPreferences
from .genetic import Genome, Rating, StopStrategy, generic_genetic_policy
from .sizes import group_sizes

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
