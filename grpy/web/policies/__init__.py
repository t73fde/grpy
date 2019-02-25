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

from typing import Type

from ..forms import RegistrationForm


class EmptyPolicyForm(RegistrationForm):
    """Form for random grouping."""


POLICY_FORMS = {
    'RD': EmptyPolicyForm,
}


def get_registration_form_class(code: str) -> Type[RegistrationForm]:
    """Return the web form for the given policy code."""
    return POLICY_FORMS.get(code, EmptyPolicyForm)
