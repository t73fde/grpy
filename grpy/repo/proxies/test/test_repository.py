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

"""Test specific for proxy repositories."""

from unittest.mock import Mock

import pytest

from ..check import CatchingProxyConnection
from ... import ProxyRepository
from ...ram import RamConnection, RamRepositoryState


class MockedProxyRepository(ProxyRepository):
    """A ProxyRepository that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


# pylint: disable=redefined-outer-name


@pytest.fixture
def proxy_repository() -> MockedProxyRepository:
    """Set up a proxy repository."""
    delegate_repository = Mock()
    delegate_repository.url = "url:"
    delegate_repository.create.return_value = RamConnection(RamRepositoryState())
    return MockedProxyRepository(delegate_repository)


def test_repository_url(proxy_repository) -> None:
    """Test that base URL is transferred to proxy repository."""
    assert proxy_repository.url == "url:"


def test_repository_can_connect(proxy_repository) -> None:
    """Test the connection to the data source."""
    proxy_repository.can_connect()
    assert proxy_repository.mock.can_connect.call_count == 1


def test_repository_initialize(proxy_repository) -> None:
    """Initialize the repository, if needed."""
    proxy_repository.initialize()
    assert proxy_repository.mock.initialize.call_count == 1


def test_repository_create(proxy_repository) -> None:
    """Create and setup a repository."""
    connection = proxy_repository.create()
    assert proxy_repository.mock.create.call_count == 1
    assert isinstance(connection, CatchingProxyConnection)
    assert not isinstance(connection, RamConnection)
