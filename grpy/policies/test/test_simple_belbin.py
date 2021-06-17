##
#    Copyright (c) 2019-2021 Detlef Stern
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

"""Tests for the simple belbin grouping policy."""

import random
from typing import cast

from ...core.models import PolicyData, User, UserKey, UserPreferences
from ..simple_belbin import (SimpleBelbinAnswer, SimpleBelbinPreferences,
                             build_simple_belbin_rating_data,
                             simple_belbin_policy)


def _create_simple_belbin_preferences() -> PolicyData:
    """Create some policy data for simple belbin preferences."""
    data = {}
    for i in range(20):
        user = User(UserKey(int=i), "user-%02d" % i)
        if i == 7:
            data[user] = UserPreferences()
        else:
            if i == 11:
                answers = cast(SimpleBelbinAnswer, (0,) * 4)
            else:
                answers = cast(
                    SimpleBelbinAnswer,
                    tuple(random.randint(0, 3) for _ in range(8)))
            data[user] = SimpleBelbinPreferences(answers)
    return data


def test_build_simple_belbin_rating_data() -> None:
    """Policy data is a function of user key to set of preferred user keys."""
    policy_data = _create_simple_belbin_preferences()
    rating_data = build_simple_belbin_rating_data(policy_data)
    for _, answers in rating_data.items():
        assert len(answers) == 8
        for answer in answers:
            assert 0 <= answer <= 3


def test_simple_belbin_policy() -> None:
    """The single preferred strategy will produce some result."""
    policy_data = _create_simple_belbin_preferences()
    for max_group_size in (4, ):
        for member_reserve in (0, 6):
            simple_belbin_policy(policy_data, max_group_size, member_reserve)
