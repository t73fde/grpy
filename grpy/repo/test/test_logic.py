
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

"""Tests for the repository logic."""

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest

from ..base import DuplicateKey, Repository
from ..logic import registration_count, set_grouping_new_code
from ...models import Grouping, Registration, User
from ...utils import now


def make_grouping() -> Grouping:
    """Build a simple grouping object."""
    yet = now()
    return Grouping(
        None, ".", "name", uuid.UUID(int=0), yet, yet + timedelta(days=7),
        None, "RD", 7, 7, "")


def test_set_grouping_new_code(repository: Repository):
    """Test the creation of new short code."""
    grouping = make_grouping()
    grouping_1 = set_grouping_new_code(repository, grouping)
    grouping_2 = set_grouping_new_code(repository, grouping)
    assert grouping_1.code != grouping_2.code


def test_set_grouping_new_code_db_error(repository: Repository):
    """Test the creation of new short codes, some repo error occurs."""
    grouping = make_grouping()
    with patch.object(repository, "set_grouping") as func:
        func.side_effect = DuplicateKey("unknown")
        with pytest.raises(DuplicateKey):
            set_grouping_new_code(repository, grouping)


def test_set_grouping_new_code_no_random(repository: Repository):
    """Test the creation of new short codes, if always the same code is made."""
    grouping = make_grouping()
    with patch.object(repository, "set_grouping") as func:
        func.side_effect = DuplicateKey("Grouping.code")
        with pytest.raises(OverflowError) as exc:
            set_grouping_new_code(repository, grouping)
        assert exc.value.args == ("grpy.repo.logic.set_grouping_new_code",)


def test_registration_count(repository: Repository):
    """Test the count calculation for a grouping."""

    # An non-existing grouping has no registrations
    assert registration_count(
        repository,
        Grouping(None, None, None, None, None, None, None, None, None, None, None)) == 0

    host = repository.set_user(User(None, "host"))
    yet = now()
    grouping = repository.set_grouping(Grouping(
        None, "code", "name", host.key, yet, yet + timedelta(days=1), None,
        'RD', 7, 7, ""))
    assert registration_count(repository, grouping) == 0

    for i in range(10):
        repository.set_registration(Registration(grouping.key, uuid.UUID(int=i), ''))
        assert registration_count(repository, grouping) == i + 1
