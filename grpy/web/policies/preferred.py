##
#    Copyright (c) 2019-2021 Detlef Stern
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

"""Web part of policy for group forming by specifying preferred members."""

from wtforms.fields import FieldList, StringField
from wtforms.validators import Length

from ...core.models import UserPreferences
from ...policies.preferred import PreferredPreferences
from ..core.forms import RegistrationForm


def create_preferred_policy_form(num_entries: int):
    """Class factory."""

    class PreferredPolicyForm(RegistrationForm):
        """Form for preferred user(s)."""

        TEMPLATE = "policies/preferred.html"

        idents = FieldList(
            StringField(
                "Ident",
                [Length(max=1000)],
                filters=[lambda s: s.strip() if s else None]),
            min_entries=num_entries, max_entries=num_entries)

        @classmethod
        def create(cls, preferences) -> RegistrationForm:
            """Create a filled form."""
            if not isinstance(preferences, PreferredPreferences):
                return cls()
            preferred = list(filter(None, preferences.preferred))
            if not preferred:
                return cls()
            return cls(idents=preferred[:num_entries])

        def get_user_preferences(self, config) -> UserPreferences:
            """Read user preferences from form."""
            if config.get('AUTH_CASE', False):
                idents = [ident for ident in self.idents.data if ident]
            else:
                idents = [ident.lower() for ident in self.idents.data if ident]
            if idents:
                return PreferredPreferences(idents)
            return PreferredPreferences([])

    return PreferredPolicyForm
