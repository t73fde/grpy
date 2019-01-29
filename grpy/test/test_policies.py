
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

"""Tests for the grouping policies."""

import pytest

from ..models import User, UserPreferences
from ..policies import (
    Policy, RandomPolicy, create_policy, get_policies, get_policy_name)


def test_group_sizes():
    """Check the different group sizes."""
    policy = Policy()
    for max_group_size in range(10):
        assert policy.group_sizes(0, max_group_size, 0) == []

    for num_p in range(10):
        assert policy.group_sizes(num_p, 1, 0) == ([1] * num_p)

    for num_r in range(10):
        assert policy.group_sizes(0, 1, num_r) == ([0] * num_r)

    test_data = (
        (1, 1, 1, [1, 0]),
        (1, 7, 3, [1]),
        (5, 5, 0, [5]),
        (5, 5, 1, [3, 2]),
        (9, 7, 2, [5, 4]),
        (9, 6, 2, [5, 4]),
        (24, 6, 5, [5, 5, 5, 5, 4]),
        (24, 6, 7, [4, 4, 4, 4, 4, 4]),
        (5, 5, 10, [3, 2, 0]),
        (45, 5, 5, [5, 5, 5, 5, 5, 4, 4, 4, 4, 4]),
        (70, 7, 5, [7, 7, 7, 7, 6, 6, 6, 6, 6, 6, 6]),
        (49, 5, 5, [5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4]),
        (33, 5, 5, [5, 4, 4, 4, 4, 4, 4, 4]),
        (40, 4, 5, [4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3]),
        (40, 4, 4, [4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3]),
        (80, 5, 10, [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 0]),
    )
    for num_p, size, num_r, result in test_data:
        assert policy.group_sizes(num_p, size, num_r) == result


def test_group_sizes_error():
    """Check the different group sizes if error values."""
    policy = Policy()
    for num_p, num_r in ((1, 0), (0, 1), (3, 1), (-1, 0), (0, -1)):
        with pytest.raises(ValueError):
            policy.group_sizes(num_p, 0, num_r)


def test_random_policy():
    """The random policy places all users into groups."""
    data = {}
    for i in range(20):
        data[User(None, "user-%d" % i)] = UserPreferences()

    policy = RandomPolicy()
    for max_group_size in range(1, 10):
        for member_reserve in range(10):
            groups = policy.build_groups(data, max_group_size, member_reserve)

            users = {user for user in data}
            for group in groups:
                assert len(group) <= max_group_size
                for member in group:
                    assert member in users
                    users.remove(member)
            assert users == set()


def test_get_policies():
    """At least there must be the random policy."""
    policies = get_policies()
    assert policies[0][1].lower() == "random"


def test_get_policy_name():
    """Always get the right name for a policy code."""
    for code, name in get_policies():
        assert name == get_policy_name(code)
    assert get_policy_name("") == ""


def test_create_policy():
    """Test to create a policy object."""
    assert create_policy("") is None
    assert create_policy('RD').NAME.lower() == "random"
