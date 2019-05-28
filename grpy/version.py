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

"""Provide version information."""

import dataclasses
import pathlib
from typing import Optional, Sequence

import pkg_resources


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class Version:
    """Version data."""

    user_version: str
    vcs_version: str
    build_date: str


def get_version_file(path: Optional[str], max_level: int) -> Sequence[str]:
    """Read the file VERSION.txt and return its content as a sequence."""
    if path:
        current_path = pathlib.Path(path)
        current_level = max_level
        while current_level > 0:
            version_path = current_path / "VERSION.txt"
            try:
                with version_path.open() as version_file:
                    return [line.strip() for line in version_file.readlines()]
            except FileNotFoundError:
                pass

            current_level -= 1
            current_path = current_path.parent
    return []


def read_version_file(path: Optional[str], max_level: int) -> Sequence[str]:
    """Read the file VERSION.txt and return its content as a sequence."""
    lines = get_version_file(path, max_level)
    if not lines:
        lines = get_version_file(".", 1)
    return lines


def get_version(lines: Sequence[str]) -> Version:
    """Return version information."""
    try:
        user_version = pkg_resources.get_distribution("grpy").version
    except pkg_resources.DistributionNotFound:
        user_version = ""
    if not lines:
        vcs_version = ""
        build_date = ""
    elif len(lines) < 2:
        vcs_version = lines[0]
        build_date = ""
    else:
        vcs_version = lines[0]
        build_date = lines[1]
    return Version(user_version, vcs_version, build_date)
