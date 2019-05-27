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

"""Test the common web forms / fields."""

import datetime

import pytz
from wtforms.form import Form

from ..app import GrpyApp
from ..forms import DateTimeField
from ..test.common import FormData


def test_date_time_field(ram_app: GrpyApp) -> None:  # pylint: disable=unused-argument
    """The date time field is time zone aware."""

    class TestForm(Form):  # pylint: disable=too-few-public-methods
        """Just a test form."""
        a = DateTimeField("a")

    form = TestForm(formdata=FormData(a="2019-05-27T16:17"))
    assert form.a.raw_data == ["2019-05-27T16:17"]
    assert form.a.data == datetime.datetime(2019, 5, 27, 14, 17, tzinfo=pytz.UTC)
    assert str(form.a) == \
        '<input id="a" name="a" type="datetime-local" value="2019-05-27T16:17">'

    form.a.raw_data = ["abc", "def"]
    assert form.a._value() == "abc def"  # pylint: disable=protected-access
    assert str(form.a) == \
        '<input id="a" name="a" type="datetime-local" value="abc def">'
