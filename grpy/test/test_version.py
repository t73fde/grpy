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

"""Test version provision."""

import pathlib
import tempfile

from ..version import Version, get_version, read_version_file


def test_read_version_file() -> None:
    """Search for a version file."""
    assert read_version_file(None, 3) == []
    with tempfile.TemporaryDirectory() as dirname:
        assert read_version_file(dirname, 1) == []
        root_path = pathlib.Path(dirname)
        with (root_path / "VERSION.txt").open("w") as version_file:
            print("user", file=version_file)
            print("vcs", file=version_file)
        assert read_version_file(dirname, 1) == ["user", "vcs"]

        subdir = root_path / "sub"
        subdir.mkdir()
        assert read_version_file(str(subdir), 1) == []
        assert read_version_file(str(subdir), 2) == ["user", "vcs"]


def test_get_version_info() -> None:
    """Test packaging of lines into data class."""
    assert get_version([]) == Version("", "")
    assert get_version(["1"]) == Version("1", "")
    assert get_version(["1", "2"]) == Version("1", "2")
    assert get_version(["1", "2", "3"]) == Version("1", "2")
