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

"""Tests for the repository logic."""

from unittest.mock import patch

import pytest

from ..base import DuplicateKey, Repository
from ..logic import set_grouping_new_code
from ...models import Grouping


def test_set_grouping_new_code(repository: Repository, grouping: Grouping):
    """Test the creation of new short code."""
    grouping_1 = set_grouping_new_code(repository, grouping)
    grouping_2 = set_grouping_new_code(repository, grouping)
    assert grouping_1.code != grouping_2.code


def test_set_grouping_new_code_db_error(repository: Repository, grouping: Grouping):
    """Test the creation of new short codes, some repo error occurs."""
    with patch.object(repository, "set_grouping") as func:
        func.side_effect = DuplicateKey("unknown")
        with pytest.raises(DuplicateKey):
            set_grouping_new_code(repository, grouping)


def test_set_grouping_new_code_no_random(repository: Repository, grouping: Grouping):
    """Test the creation of new short codes, if always the same code is made."""
    with patch.object(repository, "set_grouping") as func:
        func.side_effect = DuplicateKey("Grouping.code")
        with pytest.raises(OverflowError) as exc:
            set_grouping_new_code(repository, grouping)
        assert exc.value.args == ("grpy.repo.logic.set_grouping_new_code",)
