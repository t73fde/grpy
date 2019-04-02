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
from typing import Sequence


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class Version:
    """Version data."""

    user_version: str
    vcs_version: str


def read_version_file(path: str, max_level: int) -> Sequence[str]:
    """Read the file VERSION.txt and return its content as a sequence."""
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


def get_version_info(lines: Sequence[str]) -> Version:
    """Return version information."""
    if not lines:
        return Version("", "")
    if len(lines) < 2:
        return Version(lines[0], "")
    return Version(lines[0], lines[1])
