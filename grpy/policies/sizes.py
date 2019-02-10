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

"""Calculate group sizes."""

from typing import Sequence


def group_sizes(
        num_participants: int,
        max_group_size: int, member_reserve: int) -> Sequence[int]:
    """Return a vector of group sizes."""
    if num_participants < 0:
        raise ValueError("num_participants < 0: %d" % num_participants)
    if member_reserve < 0:
        raise ValueError("member_reserve < 0: %d" % member_reserve)
    potential_participants = num_participants + member_reserve
    if potential_participants <= 0:
        return []
    if max_group_size <= 0:
        raise ValueError("max_group_size <= 0: %d" % max_group_size)

    empty_groups = 0
    while member_reserve > max_group_size + 1:
        empty_groups += 1
        member_reserve -= max_group_size
        potential_participants -= max_group_size

    num_groups, remainder = divmod(potential_participants, max_group_size)
    if remainder > 0:
        num_groups += 1

    avg_group_size, remainder = divmod(num_participants, num_groups)
    groups = [avg_group_size + 1] * remainder + \
             [avg_group_size] * (num_groups - remainder)
    return groups + [0] * empty_groups
