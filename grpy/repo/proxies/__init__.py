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

"""Proxy reposities."""

from .check import ValidatingProxyRepository
from ..base import Repository, RepositoryFactory


class ProxyRepositoryFactory(RepositoryFactory):
    """RepositoryFactory to create ProxRepository."""

    def __init__(self, delegate: RepositoryFactory):
        """Initialize the factory with the URL."""
        super().__init__(delegate.url)
        self._delegate = delegate

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        return self._delegate.can_connect()

    def initialize(self) -> bool:
        """Initialize the repository, if needed."""
        return self._delegate.initialize()

    def create(self) -> Repository:
        """Create and setup a repository."""
        return ValidatingProxyRepository(self._delegate.create())
