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

"""Web forms for grpy user management."""

from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired


class UserPermissionsForm(FlaskForm):
    """User permissions."""

    active = BooleanField("Active")
    host = BooleanField("Host")
    manager = BooleanField("Manager")
    admin = BooleanField("Administrator")
    submit_update = SubmitField("Update")


class UserForm(FlaskForm):
    """User data."""

    ident = StringField(
        "Ident", [DataRequired()], filters=[lambda s: s.strip() if s else None])
    submit_create = SubmitField("Create")
