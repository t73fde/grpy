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
from unittest.mock import Mock

import pkg_resources

from ..version import Version, get_version, read_version_file


def test_read_version_file() -> None:
    """Search for a version file."""
    try:
        pathlib.Path("VERSION.txt").unlink()
    except FileNotFoundError:
        pass
    assert read_version_file(None, 3) == []
    with tempfile.TemporaryDirectory() as dirname:
        assert read_version_file(dirname, 1) == []
        root_path = pathlib.Path(dirname)
        with (root_path / "VERSION.txt").open("w") as version_file:
            print("vcs", file=version_file)
            print("date", file=version_file)
        assert read_version_file(dirname, 1) == ["vcs", "date"]

        subdir = root_path / "sub"
        subdir.mkdir()
        assert read_version_file(str(subdir), 1) == []
        assert read_version_file(str(subdir), 2) == ["vcs", "date"]


def test_get_version() -> None:
    """Test packaging of lines into data class."""
    try:
        version = pkg_resources.get_distribution('grpy').version
    except pkg_resources.DistributionNotFound:
        version = ""
    assert get_version([]) == Version(version, "", "")

    assert get_version(["1"]) == Version(version, "1", "")
    assert get_version(["1", "2"]) == Version(version, "1", "2")
    assert get_version(["1", "2", "3"]) == Version(version, "1", "2")


def test_get_version_from_distribution(monkeypatch) -> None:
    """Test calculating the version by using data from the distribution."""

    def get_distribution(_):
        mock = Mock()
        mock.version = "321"
        return mock

    monkeypatch.setattr(pkg_resources, 'get_distribution', get_distribution)
    assert get_version([]) == Version("321", "", "")
