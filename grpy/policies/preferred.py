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

"""Policy for group forming by specifying preferred members."""

import dataclasses  # pylint: disable=wrong-import-order
from typing import Dict, List, Set, cast

from .genetic import Genome, Rating, StopStrategy, generic_genetic_policy
from .sizes import group_sizes
from ..models import Groups, PolicyData, UserKey, UserPreferences


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
