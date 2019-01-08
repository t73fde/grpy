
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

"""Test the web utils."""

import pytest

from werkzeug.exceptions import NotFound

from .fixtures import app, auth, client  # noqa: F401 pylint: disable=unused-import
from ..utils import login_required, value_or_404


# pylint: disable=redefined-outer-name


def test_login_required(app, client, auth):  # noqa: F811
    """If no user is logged in, raise 401."""
    @login_required
    def just_a_view():
        """This view is for testing only."""
        return b"Done"

    app.add_url_rule('/test', "test", just_a_view)
    response = client.get('/test')
    assert response.status_code == 401

    auth.login("user")
    response = client.get('/test')
    assert response.status_code == 200
    assert response.data == b"Done"


def test_value_or_404():
    """A non-none value will result into value, None values raise 404."""
    for value in ([1, 2, 3], [], "", 0, (1, 2, 3)):
        assert value == value_or_404(value)


def test_value_or_404_none():
    """A none value will raise 404."""
    with pytest.raises(NotFound):
        value_or_404(None)
