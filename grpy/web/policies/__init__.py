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

from typing import List, Tuple, Type

from wtforms.fields import StringField

from ..forms import RegistrationForm


class EmptyPolicyForm(RegistrationForm):
    """Form for random grouping."""


class SinglePreferencePolicyForm(RegistrationForm):
    """Form for a single preference."""

    TEMPLATE = "policies/single_preference.html"

    ident = StringField("Ident", filters=[lambda s: s.strip() if s else None])


POLICIES: Tuple[Tuple[str, str, Type[RegistrationForm]], ...] = (
    ('RD', "Random", EmptyPolicyForm),
    ('ID', "Identity", EmptyPolicyForm),
    ('P1', "Single Preference", SinglePreferencePolicyForm),
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


def get_registration_form_class(code: str) -> Type[RegistrationForm]:
    """Return the web form for the given policy code."""
    return POLICY_FORMS.get(code, EmptyPolicyForm)
