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

from unittest.mock import Mock

import pytest

from ..check import ValidatingProxyRepository
from ... import ProxyRepositoryFactory
from ...ram import RamRepository, RamRepositoryState


class MockedProxyRepositoryFactory(ProxyRepositoryFactory):
    """A ProxyRepositoryFactory that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


# pylint: disable=redefined-outer-name


@pytest.fixture
def proxy_factory() -> MockedProxyRepositoryFactory:
    """Set up a proxy repository factory."""
    delegate_factory = Mock()
    delegate_factory.url = "url:"
    delegate_factory.create.return_value = RamRepository(RamRepositoryState())
    return MockedProxyRepositoryFactory(delegate_factory)


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
    assert isinstance(repository, ValidatingProxyRepository)
    assert not isinstance(repository, RamRepository)
