
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
from ..logic import set_grouping_new_code
from ...models import Grouping
from ...utils import now


def test_set_grouping_new_code(repository: Repository):
    """Test the creation of new short code."""
    yet = now()
    grouping = Grouping(
        None, ".", "name", uuid.UUID(int=0), yet, yet + timedelta(days=7),
        None, "RD", 7, 7, "")
    set_grouping_new_code(repository, grouping)
    set_grouping_new_code(repository, grouping)

    with patch.object(repository, "set_grouping") as func:
        func.side_effect = DuplicateKey("unknown")
        with pytest.raises(DuplicateKey):
            set_grouping_new_code(repository, grouping)
