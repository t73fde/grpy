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

"""Tests for the grouping policy by using a simple belbin test."""

from ....models import UserPreferences
from ....policies.simple_belbin import (DEFAULT_SIMPLE_BELBIN_ANSWER,
                                        SimpleBelbinPreferences)
from ..simple_belbin import SimpleBelbinPolicyForm


def test_simple_belbin_policy_form(app) -> None:  # pylint: disable=unused-argument
    """The simple belbin form contains 8 answers."""
    preferences = SimpleBelbinPolicyForm().get_user_preferences()
    assert isinstance(preferences, SimpleBelbinPreferences)
    assert preferences.answers == DEFAULT_SIMPLE_BELBIN_ANSWER

    form = SimpleBelbinPolicyForm.create(UserPreferences())
    assert isinstance(form, SimpleBelbinPolicyForm)
    assert form.answers.data == [None] * 8

    form = SimpleBelbinPolicyForm.create(SimpleBelbinPreferences(
        answers=(0, 1, 2, 3, 0, 1, 2, 3)))
    assert isinstance(form, SimpleBelbinPolicyForm)
    assert form.answers.data == [0, 1, 2, 3, 0, 1, 2, 3]
    preferences = form.get_user_preferences()
    assert isinstance(preferences, SimpleBelbinPreferences)
    assert preferences.answers == (0, 1, 2, 3, 0, 1, 2, 3)
