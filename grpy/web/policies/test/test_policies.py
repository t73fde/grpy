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

"""Tests for the grouping policies."""

from typing import List, Optional

from .. import (
    EmptyPolicyForm, PreferredPreferences, create_preferred_policy_form,
    get_policy_name, get_policy_names, get_registration_form)
from ....models import GroupingKey, Registration, UserKey, UserPreferences
from ....policies import get_policy


def test_get_policies() -> None:
    """At least there must be the random policy."""
    policies = get_policy_names()
    assert policies[0][1].lower() == "random"


def test_policies_implemented() -> None:
    """All policies defined here must have a policy func."""
    id_policy = get_policy('ID')
    for code, _ in get_policy_names():
        if code != 'ID':
            assert get_policy(code) != id_policy


def test_get_policy_name() -> None:
    """Always get the right name for a policy code."""
    for code, name in get_policy_names():
        assert name == get_policy_name(code)
    assert get_policy_name("") == ""


def test_get_registration_form(app) -> None:  # pylint: disable=unused-argument
    """The right form class must be delivered."""
    empty_policies = {'RD', 'ID'}
    for code, _ in get_policy_names():
        form = get_registration_form(code, None)
        assert form is not None
        if code not in empty_policies:
            assert not isinstance(form, EmptyPolicyForm)
    for code in empty_policies:
        assert isinstance(get_registration_form(code, None), EmptyPolicyForm)

    registration = Registration(GroupingKey(int=1), UserKey(int=2), UserPreferences())
    assert isinstance(get_registration_form('RD', registration), EmptyPolicyForm)


def test_empty_policy_form(app) -> None:  # pylint: disable=unused-argument
    """The empty policy form does nothing, mostly."""
    assert isinstance(EmptyPolicyForm().get_user_preferences(), UserPreferences)
    assert isinstance(EmptyPolicyForm.create(UserPreferences()), EmptyPolicyForm)


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
