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

"""Database layer for grpy."""

from typing import Dict, Type
from urllib.parse import urlparse

from .base import Repository
from .dummy import DummyRepository
from .proxies import ProxyRepository
from .ram import RamRepository
from .sqlite import SqliteRepository

REPOSITORY_DIRECTORY: Dict[str, Type[Repository]] = {
    "ram": RamRepository,
    "sqlite": SqliteRepository,
}


def create_repository(repository_url: str) -> Repository:
    """Create a new repository."""
    parsed_url = urlparse(repository_url)
    try:
        repository = REPOSITORY_DIRECTORY[parsed_url.scheme](parsed_url.geturl())
    except KeyError:
        repository = DummyRepository(
            "dummy:", f"Unknown repository scheme '{parsed_url.scheme}'")
    while not repository.can_connect():
        repository = DummyRepository(
            "dummy:", f"Cannot connect to {repository.url}")
    if not repository.initialize():
        repository = DummyRepository(
            "dummy:", f"Cannot initialize repository {repository.url}")
    return ProxyRepository(repository)
