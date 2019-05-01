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

"""Web part of policy for group forming by using a simple belbin test."""

from typing import cast

from wtforms.fields import FieldList, RadioField

from ...core.models import UserPreferences
from ...policies.simple_belbin import (AGREE, DEFAULT_SIMPLE_BELBIN_ANSWER,
                                       DISAGREE, SIMPLE_BELBIN_ANSWER_COUNT,
                                       STRONGLY_AGREE, STRONGLY_DISAGREE,
                                       SimpleBelbinAnswer,
                                       SimpleBelbinPreferences)
from ..forms import RegistrationForm


class SimpleBelbinPolicyForm(RegistrationForm):
    """Form for preferred user(s)."""

    TEMPLATE = "policies/simple_belbin.html"

    answers = FieldList(
        RadioField(
            "Answer",
            choices=[
                (STRONGLY_DISAGREE, "Strongly disagree"),
                (DISAGREE, "Disagree"),
                (AGREE, "Agree"),
                (STRONGLY_AGREE, "Strongly agree")],
            coerce=int),
        min_entries=SIMPLE_BELBIN_ANSWER_COUNT, max_entries=SIMPLE_BELBIN_ANSWER_COUNT)

    @classmethod
    def create(cls, preferences) -> RegistrationForm:
        """Create a filled form."""
        if not isinstance(preferences, SimpleBelbinPreferences):
            return cls()
        answers = cast(SimpleBelbinPreferences, preferences).answers
        return cls(answers=answers)

    def get_user_preferences(self, _config) -> UserPreferences:
        """Read user preferences from form."""
        if len(self.answers.data) == SIMPLE_BELBIN_ANSWER_COUNT and \
                self.answers.data != [None] * SIMPLE_BELBIN_ANSWER_COUNT:
            answers = cast(SimpleBelbinAnswer, tuple(self.answers.data))
        else:
            answers = DEFAULT_SIMPLE_BELBIN_ANSWER
        return SimpleBelbinPreferences(answers=answers)
