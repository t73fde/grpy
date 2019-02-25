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

from .. import (
    EmptyPolicyForm, PreferredPreferences, SinglePreferredPolicyForm,
    get_policy_name, get_policy_names, get_registration_form)
from ....models import GroupingKey, Registration, UserKey, UserPreferences


def test_get_policies() -> None:
    """At least there must be the random policy."""
    policies = get_policy_names()
    assert policies[0][1].lower() == "random"


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


def test_single_preferred_policy_form(app) -> None:  # pylint: disable=unused-argument
    """The single preferred policy form communicates via PreferredPreferences."""
    preferences = SinglePreferredPolicyForm().get_user_preferences()
    assert isinstance(preferences, PreferredPreferences)
    assert preferences.preferred == []
    preferences = SinglePreferredPolicyForm(ident="user").get_user_preferences()
    assert isinstance(preferences, PreferredPreferences)
    assert preferences.preferred == ["user"]

    form = SinglePreferredPolicyForm.create(preferences)
    assert isinstance(form, SinglePreferredPolicyForm)
    assert form.ident.data == "user"

    form = SinglePreferredPolicyForm.create(UserPreferences())
    assert isinstance(form, SinglePreferredPolicyForm)
    assert form.ident.data is None

    form = SinglePreferredPolicyForm.create(PreferredPreferences([]))
    assert isinstance(form, SinglePreferredPolicyForm)
    assert form.ident.data is None

    form = SinglePreferredPolicyForm.create(PreferredPreferences(["5"]))
    assert isinstance(form, SinglePreferredPolicyForm)
    assert form.ident.data == "5"

    form = SinglePreferredPolicyForm.create(PreferredPreferences(["", "7"]))
    assert isinstance(form, SinglePreferredPolicyForm)
    assert form.ident.data == "7"

    form = SinglePreferredPolicyForm.create(PreferredPreferences(["9", "7"]))
    assert isinstance(form, SinglePreferredPolicyForm)
    assert form.ident.data == "9"

    form = SinglePreferredPolicyForm.create(PreferredPreferences(["3", ""]))
    assert isinstance(form, SinglePreferredPolicyForm)
    assert form.ident.data == "3"

    form = SinglePreferredPolicyForm.create(PreferredPreferences(["", "1", "", "3"]))
    assert isinstance(form, SinglePreferredPolicyForm)
    assert form.ident.data == "1"
