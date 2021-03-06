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

"""Tests for the grouping sizes."""

import pytest

from ..sizes import group_sizes


def test_group_sizes() -> None:
    """Check the different group sizes."""
    for max_group_size in range(10):
        assert group_sizes(0, max_group_size, 0) == []

    for num_p in range(10):
        assert group_sizes(num_p, 1, 0) == ([1] * num_p)

    for num_r in range(10):
        assert group_sizes(0, 1, num_r) == ([0] * num_r)

    test_data = (
        (1, 1, 1, [1, 0]),
        (1, 7, 3, [1]),
        (5, 5, 0, [5]),
        (5, 5, 1, [3, 2]),
        (9, 7, 2, [5, 4]),
        (9, 6, 2, [5, 4]),
        (24, 6, 5, [5, 5, 5, 5, 4]),
        (24, 6, 7, [4, 4, 4, 4, 4, 4]),
        (5, 5, 10, [3, 2, 0]),
        (45, 5, 5, [5, 5, 5, 5, 5, 4, 4, 4, 4, 4]),
        (70, 7, 5, [7, 7, 7, 7, 6, 6, 6, 6, 6, 6, 6]),
        (49, 5, 5, [5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4]),
        (33, 5, 5, [5, 4, 4, 4, 4, 4, 4, 4]),
        (40, 4, 5, [4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3]),
        (40, 4, 4, [4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3]),
        (80, 5, 10, [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 0]),
    )
    for num_p, size, num_r, result in test_data:
        assert group_sizes(num_p, size, num_r) == result


def test_group_sizes_error() -> None:
    """Check the different group sizes if error values."""
    for num_p, num_r in ((1, 0), (0, 1), (3, 1), (-1, 0), (0, -1)):
        with pytest.raises(ValueError):
            group_sizes(num_p, 0, num_r)
