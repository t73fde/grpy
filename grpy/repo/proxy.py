
##
#    Copyright (c) 2018 Detlef Stern
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

"""Proxy-Repository."""

from .base import Repository


class ProxyRepository:
    """A proxy to a repository that checks create/open and close calls."""

    def __init__(self, repository: Repository):
        """Set the repository delegate."""
        self.__delegate = repository

    def close(self):
        """Close the repository."""
        self.__delegate.close()
        self.__delegate = None

    def __getattr__(self, name: str):
        """Return value of attribute, if is_open."""
        return getattr(self.__delegate, name)

    def __eq__(self, other):
        """Return True if both proxies have the same delegate."""
        return self.__delegate == other.__delegate  # pylint: disable=protected-access
