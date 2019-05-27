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

"""Common web forms and fields for grpy."""

from typing import Any, List, Optional

from flask_wtf import FlaskForm
from wtforms.fields import DateTimeField as WTFDateTimeField
from wtforms.fields import SubmitField
from wtforms.widgets.html5 import DateTimeLocalInput

from ..core.models import UserPreferences
from .utils import local2utc, utc2local


class DateTimeField(WTFDateTimeField):
    """Time zone aware date time field with better widget."""

    def __init__(
            self,
            label: str,
            validators: Optional[List[Any]] = None,
            _form=None,
            _name=None,
            _prefix="",
            _translations=None,
            _meta=None,
    ):
        """Initialize field with a label and optional validators."""
        super().__init__(
            label, validators, format="%Y-%m-%dT%H:%M", filters=[local2utc],
            widget=DateTimeLocalInput(),
            _form=_form, _name=_name, _prefix=_prefix,
            _translations=_translations, _meta=_meta,
        )

    def _value(self) -> str:
        """Provide a string representation."""
        if self.raw_data:
            return " ".join(self.raw_data)
        if self.data:
            local_data = utc2local(self.data)
            return local_data.strftime(self.format)
        return ""


class RegistrationForm(FlaskForm):
    """Base form for all registrations."""

    submit_register = SubmitField("Register")

    @classmethod
    def create(cls, preferences) -> 'RegistrationForm':
        """Create a filled form."""
        raise NotImplementedError("RegistrationForm.create")

    def get_user_preferences(self, config) -> UserPreferences:
        """Read user preferences from form."""
        raise NotImplementedError("RegistrationForm.get_user_preferences")
