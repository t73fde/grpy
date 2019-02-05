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

from datetime import timedelta

from ..logic import make_code, remove_from_groups
from ..models import Grouping, UserKey
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

    check_code(code, grouping._replace(name="Xname"))
    check_code(code, grouping._replace(begin_date=yet + timedelta(days=1)))
    check_code(code, grouping._replace(final_date=yet + timedelta(days=60)))
    check_code(code, grouping._replace(policy="LK"))
    check_code(None, grouping, unique=True)


def test_remove_from_groups() -> None:
    """Check that user key is remove from group."""
    user_key_1 = UserKey(int=1)
    user_key_2 = UserKey(int=2)

    groups_1 = (frozenset({user_key_1, user_key_2}),)
    assert remove_from_groups(groups_1, user_key_1) == (frozenset({user_key_2}),)
    assert remove_from_groups(groups_1, user_key_2) == (frozenset({user_key_1}),)

    groups_2 = (frozenset({user_key_1}), frozenset({user_key_2}))
    assert remove_from_groups(groups_2, user_key_1) == (frozenset({user_key_2}),)
    assert remove_from_groups(groups_2, user_key_2) == (frozenset({user_key_1}),)

    assert remove_from_groups(groups_1, UserKey(int=0)) == groups_1
    assert remove_from_groups(groups_2, UserKey(int=0)) == groups_2
