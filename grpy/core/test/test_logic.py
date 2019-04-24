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

"""Tests for the business logic."""

import dataclasses
from datetime import timedelta
from typing import List

from ..logic import len_groups, make_code, remove_from_groups, sort_groups
from ..models import Grouping, Groups, UserKey
from ..utils import now


def check_code(prev_code, grouping, unique=False) -> None:
    """Check for a valid code."""
    code = make_code(grouping, unique)
    assert code != prev_code

    if unique:
        assert code != make_code(grouping, True)
    else:
        assert code == make_code(grouping)
    assert code == code.upper()
    assert 1 <= len(code) <= 6
    for char in ("I", "L", "O", "U"):
        assert char not in code


def test_make_code() -> None:
    """Check the created code for simple properties."""
    yet = now()
    grouping = Grouping(
        None, ".", "name", UserKey(int=0), yet, yet + timedelta(days=7),
        None, "RD", 7, 7, "Note")
    check_code(None, grouping)
    code = make_code(grouping)

    check_code(code, dataclasses.replace(grouping, name="Xname"))
    check_code(code, dataclasses.replace(grouping, begin_date=yet + timedelta(days=1)))
    check_code(code, dataclasses.replace(grouping, final_date=yet + timedelta(days=60)))
    check_code(code, dataclasses.replace(grouping, policy="LK"))
    check_code(None, grouping, unique=True)


def _groups(spec: List[List[int]]) -> Groups:
    """Create a Group element from spec."""
    return tuple(frozenset(UserKey(int=member) for member in group) for group in spec)


def test__greoups() -> None:
    """Test _groups function."""
    assert _groups([]) == ()
    assert _groups([[0]]) == (frozenset([UserKey(int=0)]),)
    assert _groups([[0, 1]]) == (frozenset([UserKey(int=0), UserKey(int=1)]),)
    assert _groups([[0], [1]]) == (
        frozenset([UserKey(int=0)]), frozenset([UserKey(int=1)]))


def test_len_groups() -> None:
    """Calculate the len / size of groups."""
    assert len_groups(()) == 0
    assert len_groups(_groups([[0]])) == 1
    assert len_groups(_groups([[0, 1]])) == 2
    assert len_groups(_groups([[1], [2]])) == 2


def test_remove_from_groups() -> None:
    """Check that user key is remove from group."""
    user_key_1 = UserKey(int=1)
    user_key_2 = UserKey(int=2)

    groups_1 = _groups([[1, 2]])
    assert remove_from_groups(groups_1, {user_key_1}) == _groups([[2]])
    assert remove_from_groups(groups_1, {user_key_2}) == _groups([[1]])

    groups_2 = _groups([[1], [2]])
    assert remove_from_groups(groups_2, {user_key_1}) == _groups([[2]])
    assert remove_from_groups(groups_2, {user_key_2}) == _groups([[1]])

    assert remove_from_groups(groups_1, set()) == groups_1
    assert remove_from_groups(groups_1, {UserKey(int=0)}) == groups_1
    assert remove_from_groups(groups_2, set()) == groups_2
    assert remove_from_groups(groups_2, {UserKey(int=0)}) == groups_2

    assert remove_from_groups(groups_1, {user_key_1, user_key_2}) == ()
    assert remove_from_groups(groups_2, {user_key_1, user_key_2}) == ()


def test_sort_groups() -> None:
    """Groups are sorted by their user keys."""
    assert sort_groups(()) == (())
    assert sort_groups(_groups([[1]])) == _groups([[1]])
    assert sort_groups(_groups([[2], [1]])) == _groups([[1], [2]])
    assert sort_groups(_groups([[2], [3, 1]])) == _groups([[3, 1], [2]])
    assert sort_groups(_groups([[1], [3, 1]])) == _groups([[1], [1, 3]])
