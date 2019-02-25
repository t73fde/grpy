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

from wtforms.fields import StringField

from ..forms import RegistrationForm
from ...models import Registration, UserPreferences
from ...policies import PreferredPreferences


class EmptyPolicyForm(RegistrationForm):
    """Form for random grouping."""

    @classmethod
    def create(cls, preferences) -> RegistrationForm:
        """Create a filled form."""
        return cls()

    def get_user_preferences(self) -> UserPreferences:
        """Read user preferences from form."""
        return UserPreferences()


class SinglePreferredPolicyForm(RegistrationForm):
    """Form for a single preferred user."""

    TEMPLATE = "policies/single_preferred.html"

    ident = StringField("Ident", filters=[lambda s: s.strip() if s else None])

    @classmethod
    def create(cls, preferences) -> RegistrationForm:
        """Create a filled form."""
        if not isinstance(preferences, PreferredPreferences):
            return cls()
        preferred = list(filter(
            None, cast(PreferredPreferences, preferences).preferred))
        if not preferred:
            return cls()
        return cls(ident=preferred[0])

    def get_user_preferences(self) -> UserPreferences:
        """Read user preferences from form."""
        if self.ident.data:
            return PreferredPreferences([self.ident.data])
        return PreferredPreferences([])


POLICIES: Tuple[Tuple[str, str, Type[RegistrationForm]], ...] = (
    ('RD', "Random", EmptyPolicyForm),
    ('ID', "Identity", EmptyPolicyForm),
    ('P1', "Single Preference", SinglePreferredPolicyForm),
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
