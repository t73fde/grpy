
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

"""Test the web forms."""

from .fixtures import app  # noqa: F401 pylint: disable=unused-import
from ..forms import GroupingForm


# pylint: disable=redefined-outer-name


class FormData(dict):
    """A simple formdata implementation."""

    def getlist(self, key):
        """Return value as a list."""
        value = self[key]
        if not isinstance(value, (list, tuple)):
            value = [value]
        return value


def test_grouping_form(app):  # noqa: F811 pylint: disable=unused-argument
    """Validate some forms."""
    form = GroupingForm()
    form.strategy.choices = [('RD', "Random")]
    assert not form.validate()

    form = GroupingForm(formdata=FormData(
        name="name", begin_date="1970-01-01 00:00",
        final_date="1970-01-01 00:00", strategy="RD",
        max_group_size=2, member_reserve=1))
    form.strategy.choices = [('RD', "Random")]
    assert not form.validate()

    form = GroupingForm(formdata=FormData(
        name="name", begin_date="1970-01-01 00:00",
        final_date="1970-01-01 00:01", close_date="1970-01-01 00:01",
        strategy="RD", max_group_size=2, member_reserve=1))
    form.strategy.choices = [('RD', "Random")]
    assert not form.validate()

    form = GroupingForm(formdata=FormData(
        name="name", begin_date="1970-01-01 00:00",
        final_date="1970-01-01 00:01", close_date="1970-01-01 00:02",
        strategy="RD", max_group_size=2, member_reserve=1))
    form.strategy.choices = [('RD', "Random")]
    assert form.validate()
