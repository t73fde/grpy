
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

"""Tests for the business logic."""

import uuid
from datetime import timedelta

from ..logic import can_grouping_start, is_registration_open, make_code
from ..models import Grouping
from ..utils import now


def check_code(prev_code, grouping, unique=False):
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


def test_make_code():
    """Check the created code for simple properties."""
    yet = now()
    grouping = Grouping(
        None, ".", "name", uuid.UUID(int=0), yet, yet + timedelta(days=7),
        None, "RD", 7, 7, "Note")
    check_code(None, grouping)
    code = make_code(grouping)

    check_code(code, grouping._replace(name="Xname"))
    check_code(code, grouping._replace(begin_date=yet + timedelta(days=1)))
    check_code(code, grouping._replace(final_date=yet + timedelta(days=60)))
    check_code(code, grouping._replace(policy="LK"))
    check_code(None, grouping, unique=True)


def test_is_registration_open():
    """Registration is open if now is between begin and final date."""
    yet = now()
    grouping = Grouping(
        None, ".", "name", uuid.UUID(int=0), yet + timedelta(seconds=1),
        yet + timedelta(days=7), None, "RD", 7, 7, "Note")
    assert not is_registration_open(grouping)
    assert is_registration_open(grouping._replace(begin_date=yet))
    assert not is_registration_open(grouping._replace(
        begin_date=yet - timedelta(seconds=2), final_date=yet - timedelta(seconds=1)))


def test_can_grouping_start():
    """Grouping can start after the final date."""
    yet = now()
    grouping = Grouping(
        None, ".", "name", uuid.UUID(int=0), yet - timedelta(days=6),
        yet + timedelta(days=1), None, "RD", 7, 7, "Note")
    assert not can_grouping_start(grouping)
    assert can_grouping_start(grouping._replace(final_date=yet))
