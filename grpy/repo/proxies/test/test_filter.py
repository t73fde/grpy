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

"""Test specific for checking proxy repository."""

from typing import Callable
from unittest.mock import Mock

import pytest

from ..filter import FilterProxyRepository
from ...base import Repository
from ....models import (
    Grouping, GroupingKey, Registration, User, UserKey, UserPreferences)


class MockedFilterProxyRepository(FilterProxyRepository):
    """A ProxyRepository that can be mocked."""

    def __init__(self, delegate: Repository):
        """Initialize the mock."""
        super().__init__(delegate)
        self.filter_count = 0

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate

    def _filter(self, function: Callable, default, *args):
        """Execute function call and catches all relevant exceptions."""
        self.filter_count += 1
        function(*args)
        return default


@pytest.fixture
def filter_proxy() -> MockedFilterProxyRepository:
    """Set up a validating proxy repository."""
    delegate = Mock()
    delegate.return_value = 1017
    return MockedFilterProxyRepository(delegate)


# pylint: disable=redefined-outer-name


def test_get_messages(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return all repository-related messages."""
    filter_proxy.get_messages()
    assert filter_proxy.mock.get_messages.call_count == 1
    assert filter_proxy.filter_count == 1


def test_close(filter_proxy: MockedFilterProxyRepository) -> None:
    """Close the repository, store all permanent data."""
    filter_proxy.close(True)
    assert filter_proxy.mock.close.call_count == 1
    assert filter_proxy.filter_count == 1


def test_set_user(filter_proxy: MockedFilterProxyRepository) -> None:
    """Add / update the given user."""
    filter_proxy.set_user(User(None, "ident"))
    assert filter_proxy.mock.set_user.call_count == 1
    assert filter_proxy.filter_count == 1


def test_get_user(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return user for given primary key."""
    filter_proxy.get_user(UserKey(int=0))
    assert filter_proxy.mock.get_user.call_count == 1
    assert filter_proxy.filter_count == 1


def test_get_user_by_ident(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return user for given ident."""
    filter_proxy.get_user_by_ident("")
    assert filter_proxy.mock.get_user_by_ident.call_count == 1
    assert filter_proxy.filter_count == 1


def test_iter_users(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return an iterator of all or some users."""
    filter_proxy.iter_users()
    assert filter_proxy.mock.iter_users.call_count == 1
    assert filter_proxy.filter_count == 1


def test_set_grouping(
        filter_proxy: MockedFilterProxyRepository, grouping: Grouping) -> None:
    """Add / update the given grouping."""
    filter_proxy.set_grouping(grouping)
    assert filter_proxy.mock.set_grouping.call_count == 1
    assert filter_proxy.filter_count == 1


def test_get_grouping(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return grouping with given key."""
    filter_proxy.get_grouping(GroupingKey(int=0))
    assert filter_proxy.mock.get_grouping.call_count == 1
    assert filter_proxy.filter_count == 1


def test_get_grouping_by_code(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return grouping with given short code."""
    filter_proxy.get_grouping_by_code("")
    assert filter_proxy.mock.get_grouping_by_code.call_count == 1
    assert filter_proxy.filter_count == 1


def test_iter_groupings(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return an iterator of all or some groupings."""
    filter_proxy.iter_groupings()
    assert filter_proxy.mock.iter_groupings.call_count == 1
    assert filter_proxy.filter_count == 1


def test_set_registration(filter_proxy: MockedFilterProxyRepository) -> None:
    """Add / update a grouping registration."""
    filter_proxy.set_registration(
        Registration(GroupingKey(int=0), UserKey(int=0), UserPreferences()))
    assert filter_proxy.mock.set_registration.call_count == 1
    assert filter_proxy.filter_count == 1


def test_get_registration(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return registration with given grouping and user."""
    filter_proxy.get_registration(GroupingKey(int=0), UserKey(int=1))
    assert filter_proxy.mock.get_registration.call_count == 1
    assert filter_proxy.filter_count == 1


def test_count_registrations_by_grouping(
        filter_proxy: MockedFilterProxyRepository) -> None:
    """Return number of registration for given grouping."""
    filter_proxy.count_registrations_by_grouping(GroupingKey(int=0))
    assert filter_proxy.mock.count_registrations_by_grouping.call_count == 1
    assert filter_proxy.filter_count == 1


def test_delete_registration(filter_proxy: MockedFilterProxyRepository) -> None:
    """Delete the given registration from the repository."""
    filter_proxy.delete_registration(GroupingKey(int=0), UserKey(int=1))
    assert filter_proxy.mock.delete_registration.call_count == 1
    assert filter_proxy.filter_count == 1


def test_iter_groupings_by_user(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return an iterator of all groupings the user applied to."""
    filter_proxy.iter_groupings_by_user(UserKey(int=0))
    assert filter_proxy.mock.iter_groupings_by_user.call_count == 1
    assert filter_proxy.filter_count == 1


def test_iter_user_registrations_by_grouping(
        filter_proxy: MockedFilterProxyRepository) -> None:
    """Return an iterator of user data of some user."""
    filter_proxy.iter_user_registrations_by_grouping(GroupingKey(int=0))
    assert filter_proxy.mock.iter_user_registrations_by_grouping.call_count == 1
    assert filter_proxy.filter_count == 1


def test_set_groups(filter_proxy: MockedFilterProxyRepository) -> None:
    """Set / replace groups builded for grouping."""
    filter_proxy.set_groups(GroupingKey(int=0), tuple(()))
    assert filter_proxy.mock.set_groups.call_count == 1
    assert filter_proxy.filter_count == 1


def test_get_groups(filter_proxy: MockedFilterProxyRepository) -> None:
    """Get groups builded for grouping."""
    filter_proxy.get_groups(GroupingKey(int=0))
    assert filter_proxy.mock.get_groups.call_count == 1
    assert filter_proxy.filter_count == 1


def test_iter_groups_by_user(filter_proxy: MockedFilterProxyRepository) -> None:
    """Return an iterator of group data of some user."""
    filter_proxy.iter_groups_by_user(UserKey(int=0))
    assert filter_proxy.mock.iter_groups_by_user.call_count == 1
    assert filter_proxy.filter_count == 1
