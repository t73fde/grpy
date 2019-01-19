
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

"""Tests for the grouping policies."""

from ..policies import get_policies, get_policy_name


def test_get_policies():
    """At least there must be the random policy."""
    policies = get_policies()
    assert policies[0][1].lower() == "random"


def test_get_policy_name():
    """Always get the right name for a policy code."""
    for code, name in get_policies():
        assert name == get_policy_name(code)
    assert get_policy_name("") == ""
