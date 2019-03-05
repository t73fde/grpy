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

"""Tests for the grouping policy by specifying preferred members."""

from typing import cast

import pytest

from ..preferred import (
    PreferredPreferences, build_preferred_rating_data, preferred_policy)
from ...models import PolicyData, User, UserKey, UserPreferences


def _create_preferred_preferences(max_preferred: int) -> PolicyData:
    """Create some policy data for single preferred preferences."""
    data = {}
    for i in range(20):
        preferred = [
            "user-%02d" % ((i + 2 * (j + 1)) % 20) for j in range(max_preferred)]
        data[User(UserKey(int=i), "user-%02d" % i)] = PreferredPreferences(preferred)
    return cast(PolicyData, data)


def test_build_preferred_rating_data() -> None:
    """Policy data is a function of user key to set of preferred user keys."""
    for max_preferred in range(1, 9):
        policy_data = _create_preferred_preferences(max_preferred)
        rating_data = build_preferred_rating_data(policy_data, max_preferred)
        for user_key, preferred_set in rating_data.items():
            even = user_key.int % 2 == 0
            for preferred_key in preferred_set:
                assert even == (preferred_key.int % 2 == 0)

        user, _ = policy_data.popitem()
        assert user.key is not None
        policy_data[user] = UserPreferences()
        rating_data = build_preferred_rating_data(policy_data, max_preferred)
        assert rating_data[user.key] == set()


@pytest.mark.slow
def test_single_preferred_policy() -> None:
    """The single preferred strategy will produce some result."""
    for max_preferred in (1, 2, 5):
        policy_data = _create_preferred_preferences(max_preferred)
        for max_group_size in (1, 2, 4):
            for member_reserve in (0, 6):
                preferred_policy(
                    max_preferred, policy_data, max_group_size, member_reserve)
