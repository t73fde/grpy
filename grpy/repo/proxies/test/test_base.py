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

from unittest.mock import Mock

import pytest

from ..base import BaseProxyRepository
from ....models import (
    Grouping, GroupingKey, Registration, User, UserKey, UserPreferences)


class MockedBaseProxyRepository(BaseProxyRepository):
    """A ProxyRepository that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


@pytest.fixture
def base_proxy() -> MockedBaseProxyRepository:
    """Set up a validating proxy repository."""
    delegate = Mock()
    delegate.return_value = 1017
    return MockedBaseProxyRepository(delegate)


# pylint: disable=redefined-outer-name


def test_close(base_proxy: MockedBaseProxyRepository) -> None:
    """Close the repository, store all permanent data."""
    base_proxy.close()
    assert base_proxy.mock.close.call_count == 1


def test_set_user(base_proxy: MockedBaseProxyRepository) -> None:
    """Add / update the given user."""
    base_proxy.set_user(User(None, "ident"))
    assert base_proxy.mock.set_user.call_count == 1


def test_get_user(base_proxy: MockedBaseProxyRepository) -> None:
    """Return user for given primary key."""
    base_proxy.get_user(UserKey(int=0))
    assert base_proxy.mock.get_user.call_count == 1


def test_get_user_by_ident(base_proxy: MockedBaseProxyRepository) -> None:
    """Return user for given ident."""
    base_proxy.get_user_by_ident("")
    assert base_proxy.mock.get_user_by_ident.call_count == 1


def test_iter_users(base_proxy: MockedBaseProxyRepository) -> None:
    """Return an iterator of all or some users."""
    base_proxy.iter_users()
    assert base_proxy.mock.iter_users.call_count == 1


def test_set_grouping(
        base_proxy: MockedBaseProxyRepository, grouping: Grouping) -> None:
    """Add / update the given grouping."""
    base_proxy.set_grouping(grouping)
    assert base_proxy.mock.set_grouping.call_count == 1


def test_get_grouping(base_proxy: MockedBaseProxyRepository) -> None:
    """Return grouping with given key."""
    base_proxy.get_grouping(GroupingKey(int=0))
    assert base_proxy.mock.get_grouping.call_count == 1


def test_get_grouping_by_code(base_proxy: MockedBaseProxyRepository) -> None:
    """Return grouping with given short code."""
    base_proxy.get_grouping_by_code("")
    assert base_proxy.mock.get_grouping_by_code.call_count == 1


def test_iter_groupings(base_proxy: MockedBaseProxyRepository) -> None:
    """Return an iterator of all or some groupings."""
    base_proxy.iter_groupings()
    assert base_proxy.mock.iter_groupings.call_count == 1


def test_set_registration(base_proxy: MockedBaseProxyRepository) -> None:
    """Add / update a grouping registration."""
    base_proxy.set_registration(
        Registration(GroupingKey(int=0), UserKey(int=0), UserPreferences()))
    assert base_proxy.mock.set_registration.call_count == 1


def test_get_registration(base_proxy: MockedBaseProxyRepository) -> None:
    """Return registration with given grouping and user."""
    base_proxy.get_registration(GroupingKey(int=0), UserKey(int=1))
    assert base_proxy.mock.get_registration.call_count == 1


def test_count_registrations_by_grouping(base_proxy: MockedBaseProxyRepository) -> None:
    """Return number of registration for given grouping."""
    base_proxy.count_registrations_by_grouping(GroupingKey(int=0))
    assert base_proxy.mock.count_registrations_by_grouping.call_count == 1


def test_delete_registration(base_proxy: MockedBaseProxyRepository) -> None:
    """Delete the given registration from the repository."""
    base_proxy.delete_registration(GroupingKey(int=0), UserKey(int=1))
    assert base_proxy.mock.delete_registration.call_count == 1


def test_iter_groupings_by_user(base_proxy: MockedBaseProxyRepository) -> None:
    """Return an iterator of all groupings the user applied to."""
    base_proxy.iter_groupings_by_user(UserKey(int=0))
    assert base_proxy.mock.iter_groupings_by_user.call_count == 1


def test_iter_user_registrations_by_grouping(
        base_proxy: MockedBaseProxyRepository) -> None:
    """Return an iterator of user data of some user."""
    base_proxy.iter_user_registrations_by_grouping(GroupingKey(int=0))
    assert base_proxy.mock.iter_user_registrations_by_grouping.call_count == 1


def test_set_groups(base_proxy: MockedBaseProxyRepository) -> None:
    """Set / replace groups builded for grouping."""
    base_proxy.set_groups(GroupingKey(int=0), tuple(()))
    assert base_proxy.mock.set_groups.call_count == 1


def test_get_groups(base_proxy: MockedBaseProxyRepository) -> None:
    """Get groups builded for grouping."""
    base_proxy.get_groups(GroupingKey(int=0))
    assert base_proxy.mock.get_groups.call_count == 1


def test_iter_groups_by_user(base_proxy: MockedBaseProxyRepository) -> None:
    """Return an iterator of group data of some user."""
    base_proxy.iter_groups_by_user(UserKey(int=0))
    assert base_proxy.mock.iter_groups_by_user.call_count == 1