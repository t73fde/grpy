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

"""Web part of policies for group forming."""

from typing import List, Optional, Tuple, Type, cast

from wtforms.fields import FieldList, RadioField, StringField

from ..forms import RegistrationForm
from ...models import Registration, UserPreferences
from ...policies import (
    AGREE, DEFAULT_SIMPLE_BELBIN_ANSWER, DISAGREE, PreferredPreferences,
    SIMPLE_BELBIN_ANSWER_COUNT, STRONGLY_AGREE, STRONGLY_DISAGREE,
    SimpleBelbinAnswer, SimpleBelbinPreferences)


class EmptyPolicyForm(RegistrationForm):
    """Form for random grouping."""

    @classmethod
    def create(cls, preferences) -> RegistrationForm:
        """Create a filled form."""
        return cls()

    def get_user_preferences(self) -> UserPreferences:
        """Read user preferences from form."""
        return UserPreferences()


def create_preferred_policy_form(num_entries: int):
    """Class factory."""

    class PreferredPolicyForm(RegistrationForm):
        """Form for preferred user(s)."""

        TEMPLATE = "policies/preferred.html"

        idents = FieldList(
            StringField("Ident", filters=[lambda s: s.strip() if s else None]),
            min_entries=num_entries, max_entries=num_entries)

        @classmethod
        def create(cls, preferences) -> RegistrationForm:
            """Create a filled form."""
            if not isinstance(preferences, PreferredPreferences):
                return cls()
            preferred = list(filter(
                None, cast(PreferredPreferences, preferences).preferred))
            if not preferred:
                return cls()
            return cls(idents=preferred[:num_entries])

        def get_user_preferences(self) -> UserPreferences:
            """Read user preferences from form."""
            idents = [ident for ident in self.idents.data if ident]
            if idents:
                return PreferredPreferences(idents)
            return PreferredPreferences([])

    return PreferredPolicyForm


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

    def get_user_preferences(self) -> UserPreferences:
        """Read user preferences from form."""
        if len(self.answers.data) == SIMPLE_BELBIN_ANSWER_COUNT and \
                self.answers.data != [None] * SIMPLE_BELBIN_ANSWER_COUNT:
            answers = cast(SimpleBelbinAnswer, tuple(self.answers.data))
        else:
            answers = DEFAULT_SIMPLE_BELBIN_ANSWER
        return SimpleBelbinPreferences(answers=answers)


POLICIES: Tuple[Tuple[str, str, Type[RegistrationForm]], ...] = (
    ('RD', "Random", EmptyPolicyForm),
    ('ID', "Identity", EmptyPolicyForm),
    ('P1', "Single Preference", create_preferred_policy_form(1)),
    ('P2', "Double Preference", create_preferred_policy_form(2)),
    ('P3', "Triple Preference", create_preferred_policy_form(3)),
    ('SB', "Simple Belbin", SimpleBelbinPolicyForm),
)
POLICY_META = [(code, name) for (code, name, _) in POLICIES]
POLICY_NAMES = dict(POLICY_META)
POLICY_FORMS = {code: func for (code, _, func) in POLICIES}


def get_policy_names() -> List[Tuple[str, str]]:
    """Return list of policies."""
    return list(POLICY_META)


def get_policy_name(code: str) -> str:
    """Return policy name for given code."""
    return POLICY_NAMES.get(code, "")


def get_registration_form(
        code: str, registration: Optional[Registration]) -> RegistrationForm:
    """Return the web form for the given policy code."""
    form_class = POLICY_FORMS.get(code, EmptyPolicyForm)
    if registration is None:
        return form_class()
    return form_class.create(registration.preferences)
