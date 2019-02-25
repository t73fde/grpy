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

"""Tests for the grouping policies."""

from typing import Set, cast

from .. import (
    PreferredPreferences, build_preferred_rating_data, get_policy,
    identity_policy, preferred_policy, random_policy)
from ...models import Groups, PolicyData, User, UserKey, UserPreferences


def assert_members_and_sizes(
        groups: Groups, users: Set[UserKey], max_group_size: int) -> None:
    """Assert that group contains all users and have descending group size."""
    last_size = max_group_size
    for group in groups:
        assert len(group) <= max_group_size
        assert len(group) <= last_size
        last_size = len(group)
        for member in group:
            assert member in users
            users.remove(member)
    assert users == set()


def test_identity_policy() -> None:
    """The no policy places all users into groups by name."""
    data = {}
    repository = {}
    for i in range(20):
        user = User(UserKey(int=i), "user-%03d" % i)
        repository[user.key] = user
        data[user] = UserPreferences()

    for max_group_size in range(1, 10):
        for member_reserve in range(10):
            groups = identity_policy(data, max_group_size, member_reserve)
            users = cast(Set[UserKey], {user.key for user in data})
            assert_members_and_sizes(groups, users, max_group_size)
            last_ident = ""
            for group in groups:
                idents = [repository[member].ident for member in group]
                if idents:
                    assert last_ident < min(idents)
                    last_ident = max(idents)
                else:
                    last_ident = chr(65536)


def test_random_policy() -> None:
    """The random policy places all users into groups."""
    data = {}
    for i in range(20):
        data[User(UserKey(int=i), "user-%d" % i)] = UserPreferences()

    for max_group_size in range(1, 10):
        for member_reserve in range(10):
            groups = random_policy(data, max_group_size, member_reserve)
            users = cast(Set[UserKey], {user.key for user in data})
            assert_members_and_sizes(groups, users, max_group_size)


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


def test_single_preferred_policy() -> None:
    """The single preferred strategy will produce some result."""
    for max_preferred in (1, 2, 5):
        policy_data = _create_preferred_preferences(max_preferred)
        for max_group_size in (1, 2, 4):
            for member_reserve in (0, 6):
                preferred_policy(
                    max_preferred, policy_data, max_group_size, member_reserve)


def test_create_policy() -> None:
    """Test to create a policy object."""
    for code in ('', ' ', '____'):
        assert get_policy(code) is identity_policy
    assert get_policy('RD') is random_policy
