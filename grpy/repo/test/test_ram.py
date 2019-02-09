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

"""Test the specifics of RAM-based repositories."""

from ..ram import RamRepository


def test_url() -> None:
    """The URL of the repository is that of the init argument."""
    assert RamRepository("ram:").url == "ram:"


def test_always_other_repository() -> None:
    """The repository will always return another connection."""
    repository = RamRepository("")
    connection_1 = repository.create()
    connection_2 = repository.create()
    assert connection_1 != connection_2


def test_different_repositories_different_connections() -> None:
    """Different repositories create different connections."""
    repository_1 = RamRepository("")
    connection_1 = repository_1.create()
    repository_2 = RamRepository("")
    connection_2 = repository_2.create()
    assert connection_1 is not connection_2
    assert connection_1 != connection_2
