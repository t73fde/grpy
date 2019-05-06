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
from wtforms.fields import (BooleanField, HiddenField, PasswordField,
                            StringField, SubmitField)
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):  # pylint: disable=too-few-public-methods
    """Login data."""

    username = StringField("Username", [DataRequired()])
    password = PasswordField("Password", [DataRequired()])
    next_url = HiddenField()
    submit_login = SubmitField("Login")


class UserPermissionsForm(FlaskForm):
    """User permissions."""

    active = BooleanField("Active")
    host = BooleanField("Host")
    admin = BooleanField("Administrator")
    submit_update = SubmitField("Update")
