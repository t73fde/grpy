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
    get_policy, get_policy_name, get_policy_names, identity_policy, random_policy)
from ...models import Groups, User, UserKey, UserPreferences


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


def test_get_policies() -> None:
    """At least there must be the random policy."""
    policies = get_policy_names()
    assert policies[0][1].lower() == "random"


def test_get_policy_name() -> None:
    """Always get the right name for a policy code."""
    for code, name in get_policy_names():
        assert name == get_policy_name(code)
    assert get_policy_name("") == ""


def test_create_policy() -> None:
    """Test to create a policy object."""
    for code in ('', ' ', '____'):
        assert get_policy(code) is identity_policy
    assert get_policy('RD') is random_policy
