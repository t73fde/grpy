
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

"""Test the specifics of dummy repositories."""

from ..dummy import DummyRepositoryFactory


def test_url() -> None:
    """The URL of the Factory is that of the init argument."""
    assert DummyRepositoryFactory("dummy:").url == "dummy:"


def test_different_repository() -> None:
    """The factory will always return different repositories."""
    factory = DummyRepositoryFactory("")
    repo_1 = factory.create()
    repo_2 = factory.create()
    assert repo_1 is not repo_2
