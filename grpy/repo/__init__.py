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

from .base import RepositoryFactory
from .dummy import DummyRepositoryFactory
from .ram import RamRepositoryFactory
from .sqlite import SqliteRepositoryFactory


FACTORY_DIRECTORY: Dict[str, Type[RepositoryFactory]] = {
    "ram": RamRepositoryFactory,
    "sqlite": SqliteRepositoryFactory,
}


def create_factory(repository_url: str) -> RepositoryFactory:
    """Create a new repository."""
    parsed_url = urlparse(repository_url)
    try:
        factory = FACTORY_DIRECTORY[parsed_url.scheme](parsed_url.geturl())
    except KeyError:
        factory = DummyRepositoryFactory(
            "dummy:", "Unknown repository scheme '{}'".format(parsed_url.scheme))
    while not factory.can_connect():
        factory = DummyRepositoryFactory(
            "dummy:", "Cannot connect to {}".format(factory.url))
    if not factory.initialize():
        factory = DummyRepositoryFactory(
            "dummy:", "Cannot initialize repository {}".format(factory.url))
    return factory
