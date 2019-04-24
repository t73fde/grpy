##
#    Copyright (c) 2018,2019 Detlef Stern
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

"""Common web forms for grpy."""

from flask_wtf import FlaskForm
from wtforms.fields import SubmitField

from ..models import UserPreferences


class RegistrationForm(FlaskForm):
    """Base form for all registrations."""

    submit_register = SubmitField("Register")

    @classmethod
    def create(cls, preferences) -> 'RegistrationForm':
        """Create a filled form."""
        raise NotImplementedError("RegistrationForm.create")

    def get_user_preferences(self) -> UserPreferences:
        """Read user preferences from form."""
        raise NotImplementedError("RegistrationForm.get_user_preferences")
