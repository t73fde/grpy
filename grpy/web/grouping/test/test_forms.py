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

"""Test the web forms for groupings."""

from ...test.common import FormData
from ..forms import GroupingForm


def test_grouping_form(ram_app) -> None:  # pylint: disable=unused-argument
    """Validate some forms."""
    form = GroupingForm()
    form.policy.choices = [('RD', "Random")]
    assert not form.validate()
    assert form.errors == {
        'name': ["This field is required."],
        'begin_date': ["This field is required."],
        'final_date': ["This field is required."],
        'max_group_size': ["This field is required."],
        'member_reserve': ["This field is required."],
        'policy': ["Not a valid choice"],
    }

    form = GroupingForm(formdata=FormData(
        name="n", begin_date="n", final_date="n", policy="n",
        max_group_size="n", member_reserve="n", note=""))
    form.policy.choices = [('RD', "Random")]
    assert not form.validate()
    assert form.errors == {
        'begin_date': ["Not a valid datetime value"],
        'final_date': ["Not a valid datetime value"],
        'max_group_size': ["Not a valid integer value", "Number must be at least 1."],
        'member_reserve': ["Not a valid integer value", "Number must be at least 0."],
        'policy': ["Not a valid choice"],
    }

    form = GroupingForm(formdata=FormData(
        name="name", begin_date="1970-01-01 00:00",
        final_date="1970-01-01 00:00", policy="RD",
        max_group_size=2, member_reserve=1, note="Note"))
    form.policy.choices = [('RD', "Random")]
    assert not form.validate()
    assert form.errors == {
        'final_date': ["Final date must be after begin date."],
    }

    form = GroupingForm(formdata=FormData(
        name="name" * 1000, begin_date="1970-01-01 00:00",
        final_date="1970-01-01 00:01", close_date="1970-01-01 00:01",
        policy="RD", max_group_size=2, member_reserve=1, note="Notes" * 1000))
    form.policy.choices = [('RD', "Random")]
    assert not form.validate()
    assert form.errors == {
        'name': ["Field cannot be longer than 1000 characters."],
        'close_date': ["Close date must be after final date."],
        'note': ["Field cannot be longer than 2000 characters."],
    }

    form = GroupingForm(formdata=FormData(
        name="name", begin_date="1970-01-01 00:00",
        final_date="1970-01-01 00:01", close_date="1970-01-01 00:02",
        policy="RD", max_group_size=2, member_reserve=1, notes=""))
    form.policy.choices = [('RD', "Random")]
    assert form.validate()
