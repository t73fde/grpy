
##
#    Copyright (c) 2018 Detlef Stern
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

"""Web forms for grpy."""

from flask_wtf import FlaskForm

from pytz import UTC

from wtforms.fields import (
    DateTimeField, HiddenField, IntegerField, PasswordField, SelectField, StringField)
from wtforms.validators import (
    DataRequired, InputRequired, NumberRange, Optional, ValidationError)
from wtforms.widgets import TextArea


class LoginForm(FlaskForm):  # pylint: disable=too-few-public-methods
    """Login data."""

    username = StringField("Username", [DataRequired()])
    password = PasswordField("Password", [DataRequired()])
    next_url = HiddenField()


class GroupingForm(FlaskForm):
    """Grouping data."""

    name = StringField(
        "Name", [DataRequired()], filters=[lambda s: s.strip() if s else None])
    begin_date = DateTimeField(
        "Begin date", [InputRequired()],
        filters=[lambda d: d.replace(tzinfo=UTC) if d else None],
        format="%Y-%m-%d %H:%M")
    final_date = DateTimeField(
        "Final date", [InputRequired()],
        filters=[lambda d: d.replace(tzinfo=UTC) if d else None],
        format="%Y-%m-%d %H:%M")
    close_date = DateTimeField(
        "Close date", [Optional()],
        filters=[lambda d: d.replace(tzinfo=UTC) if d else None],
        format="%Y-%m-%d %H:%M")
    strategy = SelectField("Strategy", [DataRequired()])
    max_group_size = IntegerField(
        "Maximum group size", [InputRequired(), NumberRange(min=1)])
    member_reserve = IntegerField(
        "Member reserve", [InputRequired(), NumberRange(min=0)])
    note = StringField(
        "Notes", widget=TextArea(), filters=[lambda s: s.strip() if s else None])

    def validate_final_date(self, field):
        """Check that final date is after begin date."""
        if self.begin_date.data and field.data and self.begin_date.data >= field.data:
            raise ValidationError("Final date must be after begin date.")

    def validate_close_date(self, field):
        """Close date must be after final date."""
        if self.final_date.data >= field.data:
            raise ValidationError("Close date must be after final date.")


class ApplicationForm(FlaskForm):
    """Base form for all applications."""
