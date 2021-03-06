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

from ..base import Connection, Repository
from .check import CatchingProxyConnection, ValidatingProxyConnection


class ProxyRepository(Repository):
    """Repository to create ProxyConnection."""

    def __init__(self, delegate: Repository):
        """Initialize the repository with the proxied repository."""
        super().__init__(delegate.url)
        self._delegate = delegate

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        return self._delegate.can_connect()

    def initialize(self) -> bool:
        """Initialize the repository, if needed."""
        return self._delegate.initialize()

    def create(self) -> Connection:
        """Create and setup a connection."""
        return CatchingProxyConnection(
            ValidatingProxyConnection(self._delegate.create()))
