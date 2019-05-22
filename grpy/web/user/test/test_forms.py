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

"""Test the web forms for user management."""

from ...test.common import FormData
from ..forms import UserForm


def test_user_form(ram_app) -> None:  # pylint: disable=unused-argument
    """Validate the login form."""
    form = UserForm()
    assert not form.validate()
    assert form.errors == {
        'ident': ["This field is required."],
    }

    form = UserForm(formdata=FormData(ident="1" * 2000))
    assert not form.validate()
    assert form.errors == {
        'ident': ["Field cannot be longer than 1000 characters."],
    }
