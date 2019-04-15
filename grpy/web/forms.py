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

"""Web forms for grpy."""

from flask_wtf import FlaskForm
from pytz import UTC
from wtforms.fields import (DateTimeField, IntegerField, SelectField,
                            StringField, SubmitField)
from wtforms.validators import (DataRequired, InputRequired, NumberRange,
                                Optional, ValidationError)
from wtforms.widgets import TextArea

from ..models import UserPreferences


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
    policy = SelectField("Policy", [DataRequired()])
    max_group_size = IntegerField(
        "Maximum group size", [InputRequired(), NumberRange(min=1)])
    member_reserve = IntegerField(
        "Member reserve", [InputRequired(), NumberRange(min=0)])
    note = StringField(
        "Notes", widget=TextArea(), filters=[lambda s: s.strip() if s else ""])
    submit_create = SubmitField("Create")
    submit_update = SubmitField("Update")
    submit_delete = SubmitField("Delete")

    def validate_final_date(self, field):
        """Check that final date is after begin date."""
        if self.begin_date.data and field.data and self.begin_date.data >= field.data:
            raise ValidationError("Final date must be after begin date.")

    def validate_close_date(self, field):
        """Close date must be after final date."""
        if self.final_date.data >= field.data:
            raise ValidationError("Close date must be after final date.")


class StartGroupingForm(FlaskForm):
    """Form to start the group building process."""

    submit_start = SubmitField("Start")


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


class RemoveRegistrationsForm(FlaskForm):
    """
    Form to remove registrations.

    Note: WTForms does not allow to user FieldList with BooleanField.  We do it
    on our own. This form is needed to protet against CSRF-Attacks.
    """

    submit_remove = SubmitField("Remove")


class RemoveGroupsForm(FlaskForm):
    """Form to remove the formed groups."""

    submit_remove = SubmitField("Remove")
    submit_cancel = SubmitField("Cancel")


class FastenGroupsForm(FlaskForm):
    """Form to fasten the formed groups by removing all registrations."""

    submit_fasten = SubmitField("Fasten")
    submit_cancel = SubmitField("Cancel")
