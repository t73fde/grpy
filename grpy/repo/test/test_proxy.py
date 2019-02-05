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

"""Test specific for proxy repository."""

import uuid
from typing import cast
from unittest.mock import Mock

import pytest

from ..proxy import ProxyRepository, ProxyRepositoryFactory
from ...models import (
    Grouping, GroupingKey, Registration, User, UserKey, UserPreferences,
    ValidationFailed)


class MockedProxyRepository(ProxyRepository):
    """A ProxyRepository that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


@pytest.fixture
def proxy() -> MockedProxyRepository:
    """Set up a proxy repository."""
    delegate = Mock()
    delegate.return_value = 1017
    return MockedProxyRepository(delegate)


class MockedProxyRepositoryFactory(ProxyRepositoryFactory):
    """A ProxyRepositoryFactory that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


# pylint: disable=redefined-outer-name


@pytest.fixture
def proxy_factory(proxy) -> MockedProxyRepositoryFactory:
    """Set up a proxy repository factory."""
    delegate_factory = Mock()
    delegate_factory.url = "url:"
    delegate_factory.create.return_value = proxy
    return MockedProxyRepositoryFactory(delegate_factory)


def test_close(proxy: MockedProxyRepository) -> None:
    """Close the repository, store all permanent data."""
    proxy.close()
    assert proxy.mock.close.call_count == 1


def test_set_user(proxy: MockedProxyRepository) -> None:
    """Add / update the given user."""
    proxy.set_user(User(None, "ident"))
    assert proxy.mock.set_user.call_count == 1


def test_get_user(proxy: MockedProxyRepository) -> None:
    """Return user for given primary key."""
    proxy.get_user(UserKey(int=0))
    assert proxy.mock.get_user.call_count == 1


def test_get_user_by_ident(proxy: MockedProxyRepository) -> None:
    """Return user for given ident."""
    proxy.get_user_by_ident("")
    assert proxy.mock.get_user_by_ident.call_count == 1


def test_iter_users(proxy: MockedProxyRepository) -> None:
    """Return an iterator of all or some users."""
    proxy.iter_users()
    assert proxy.mock.iter_users.call_count == 1


def test_set_grouping(proxy: MockedProxyRepository, grouping: Grouping) -> None:
    """Add / update the given grouping."""
    proxy.set_grouping(grouping)
    assert proxy.mock.set_grouping.call_count == 1


def test_get_grouping(proxy: MockedProxyRepository) -> None:
    """Return grouping with given key."""
    proxy.get_grouping(GroupingKey(int=0))
    assert proxy.mock.get_grouping.call_count == 1


def test_get_grouping_by_code(proxy: MockedProxyRepository) -> None:
    """Return grouping with given short code."""
    proxy.get_grouping_by_code("")
    assert proxy.mock.get_grouping_by_code.call_count == 1


def test_iter_groupings(proxy: MockedProxyRepository) -> None:
    """Return an iterator of all or some groupings."""
    proxy.iter_groupings()
    assert proxy.mock.iter_groupings.call_count == 1


def test_set_registration(proxy: MockedProxyRepository) -> None:
    """Add / update a grouping registration."""
    proxy.set_registration(
        Registration(GroupingKey(int=0), UserKey(int=0), UserPreferences()))
    assert proxy.mock.set_registration.call_count == 1


def test_get_registration(proxy: MockedProxyRepository) -> None:
    """Return registration with given grouping and user."""
    proxy.get_registration(GroupingKey(int=0), UserKey(int=1))
    assert proxy.mock.get_registration.call_count == 1


def test_count_registrations_by_grouping(proxy: MockedProxyRepository) -> None:
    """Return number of registration for given grouping."""
    proxy.count_registrations_by_grouping(GroupingKey(int=0))
    assert proxy.mock.count_registrations_by_grouping.call_count == 1


def test_delete_registration(proxy: MockedProxyRepository) -> None:
    """Delete the given registration from the repository."""
    proxy.delete_registration(GroupingKey(int=0), UserKey(int=1))
    assert proxy.mock.delete_registration.call_count == 1


def test_iter_groupings_by_user(proxy: MockedProxyRepository) -> None:
    """Return an iterator of all groupings the user applied to."""
    proxy.iter_groupings_by_user(UserKey(int=0))
    assert proxy.mock.iter_groupings_by_user.call_count == 1


def test_iter_user_registrations_by_grouping(proxy: MockedProxyRepository) -> None:
    """Return an iterator of user data of some user."""
    proxy.iter_user_registrations_by_grouping(GroupingKey(int=0))
    assert proxy.mock.iter_user_registrations_by_grouping.call_count == 1


def test_set_groups(proxy: MockedProxyRepository) -> None:
    """Set / replace groups builded for grouping."""
    proxy.set_groups(GroupingKey(int=0), tuple(()))
    assert proxy.mock.set_groups.call_count == 1


def test_set_groups_no_validation(proxy: MockedProxyRepository) -> None:
    """Set / replace groups builded for grouping."""
    with pytest.raises(ValidationFailed, match="Group member is not an UserKey: None"):
        proxy.set_groups(GroupingKey(int=0), (frozenset({cast(UserKey, None)}),))
    assert proxy.mock.set_groups.call_count == 0
    with pytest.raises(
            ValidationFailed, match=r"Group member is not an UserKey: UUID\('"):
        proxy.set_groups(
            GroupingKey(int=0), (frozenset({cast(UserKey, uuid.uuid4())}),))
    assert proxy.mock.set_groups.call_count == 0
    with pytest.raises(
            ValidationFailed, match=r"Group member is not an UserKey: GroupingKey\('"):
        proxy.set_groups(
            GroupingKey(int=0), (frozenset({cast(UserKey, GroupingKey())}),))
    assert proxy.mock.set_groups.call_count == 0


def test_get_groups(proxy: MockedProxyRepository) -> None:
    """Get groups builded for grouping."""
    proxy.get_groups(GroupingKey(int=0))
    assert proxy.mock.get_groups.call_count == 1


def test_iter_groups_by_user(proxy: MockedProxyRepository) -> None:
    """Return an iterator of group data of some user."""
    proxy.iter_groups_by_user(UserKey(int=0))
    assert proxy.mock.iter_groups_by_user.call_count == 1


def test_factory_url(proxy_factory) -> None:
    """Test that base URL is transferred to proxy factory."""
    assert proxy_factory.url == "url:"


def test_factory_can_connect(proxy_factory) -> None:
    """Test the connection to the data source."""
    proxy_factory.can_connect()
    assert proxy_factory.mock.can_connect.call_count == 1


def test_factory_initialize(proxy_factory) -> None:
    """Initialize the repository, if needed."""
    proxy_factory.initialize()
    assert proxy_factory.mock.initialize.call_count == 1


def test_factory_create(proxy_factory) -> None:
    """Create and setup a repository."""
    repository = proxy_factory.create()
    assert proxy_factory.mock.create.call_count == 1
    assert isinstance(repository, ProxyRepository)
    assert not isinstance(repository, MockedProxyRepository)