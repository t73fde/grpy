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

"""Tests for the grouping policy by specifying preferred members."""

from typing import List, Optional

from ....models import UserPreferences
from ....policies.preferred import PreferredPreferences
from ..preferred import create_preferred_policy_form


def assert_idents(
        data: List[Optional[str]], size: int, values: List[Optional[str]]) -> None:
    """Check the data from PreferredForm."""
    assert data == values[:size] + [None] * (size - len(values))


def test_preferred_policy_form(app) -> None:  # pylint: disable=unused-argument
    """The preferred policy form communicates via PreferredPreferences."""
    for i in range(5):
        PreferredPolicyForm = create_preferred_policy_form(i)
        preferences = PreferredPolicyForm().get_user_preferences()
        assert isinstance(preferences, PreferredPreferences)
        assert preferences.preferred == []

        form = PreferredPolicyForm.create(UserPreferences())
        assert isinstance(form, PreferredPolicyForm)
        assert form.idents.data == [None] * i

        form = PreferredPolicyForm.create(PreferredPreferences([]))
        assert isinstance(form, PreferredPolicyForm)
        assert form.idents.data == [None] * i

        preferences = PreferredPolicyForm(idents=["user"]).get_user_preferences()
        assert isinstance(preferences, PreferredPreferences)
        assert preferences.preferred == ["user"]

        form = PreferredPolicyForm.create(preferences)
        assert isinstance(form, PreferredPolicyForm)
        assert_idents(form.idents.data, i, ["user"])

        form = PreferredPolicyForm.create(PreferredPreferences(["5"]))
        assert isinstance(form, PreferredPolicyForm)
        assert_idents(form.idents.data, i, ["5"])

        form = PreferredPolicyForm.create(PreferredPreferences(["", "7"]))
        assert isinstance(form, PreferredPolicyForm)
        assert_idents(form.idents.data, i, ["7"])

        form = PreferredPolicyForm.create(PreferredPreferences(["9", "7"]))
        assert isinstance(form, PreferredPolicyForm)
        assert_idents(form.idents.data, i, ["9", "7"])

        form = PreferredPolicyForm.create(PreferredPreferences(["3", ""]))
        assert isinstance(form, PreferredPolicyForm)
        assert_idents(form.idents.data, i, ["3"])

        form = PreferredPolicyForm.create(PreferredPreferences(["", "1", "", "3"]))
        assert isinstance(form, PreferredPolicyForm)
        assert_idents(form.idents.data, i, ["1", "3"])
