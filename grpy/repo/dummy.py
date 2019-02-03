##
#    Copyright (c) 2018,2019 Detlef Stern
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

"""Dummy repository, used for error handling."""

from typing import Optional

from .base import Repository, RepositoryFactory
from .ram import RamRepository, RamRepositoryState


class DummyRepositoryFactory(RepositoryFactory):
    """Create dummy repositories."""

    def __init__(self, repository_url: str, reason: Optional[str] = None):
        """Initialize the factory."""
        super().__init__(repository_url)
        self._reason = reason

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        return True

    def initialize(self) -> bool:
        """Initialize the repository, if needed."""
        return True

    def create(self) -> Repository:
        """Create a new dummy repository."""
        return RamRepository(RamRepositoryState())
