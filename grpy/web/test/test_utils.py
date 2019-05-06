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

"""Test the web utils."""

import dataclasses
import datetime

import pytest
from flask import url_for
from werkzeug.exceptions import NotFound
from werkzeug.test import Client

from ...core.models import GroupingKey, Permissions, User, UserKey
from ...core.utils import now
from ..app import GrpyApp, create_app
from ..middleware import PrefixMiddleware
from ..utils import (admin_required, datetimeformat, login_required,
                     login_required_redirect, make_model, to_bool,
                     update_model, value_or_404)


def test_grouping_key_converter(ram_app: GrpyApp, ram_client) -> None:
    """Make sure that the URL converter 'grouping' works as expected."""

    def just_a_view(grouping_key: GroupingKey) -> bytes:
        """This view is for testing only."""
        assert isinstance(grouping_key, GroupingKey)
        assert grouping_key.int == 1017
        return b"Done"

    ram_app.add_url_rule('/test<grouping:grouping_key>/', "test_view", just_a_view)
    response = ram_client.get(url_for(
        "test_view", grouping_key=str(GroupingKey(int=1017))))
    assert response.status_code == 200
    assert response.data == b"Done"


def test_to_bool() -> None:
    """The `to_bool` function should deliver useful values."""
    assert to_bool(None) is False
    assert to_bool(True) is True
    assert to_bool(False) is False

    assert to_bool(0) is False
    assert to_bool(1) is True

    assert to_bool("") is False
    assert to_bool("0") is False
    assert to_bool("falsch") is False
    assert to_bool("False") is False

    assert to_bool("1") is True
    assert to_bool("Yes") is True


def _make_user_inactive(ram_app: GrpyApp, ident: str) -> None:
    """Make user with given ident inactive."""
    user = ram_app.get_connection().get_user_by_ident(ident)
    assert user is not None
    ram_app.get_connection().set_user(dataclasses.replace(
        user,
        permissions=user.permissions | Permissions.INACTIVE))


def test_login_required(ram_app: GrpyApp, ram_client, ram_auth) -> None:
    """If no user is logged in, raise 401."""
    @login_required
    def just_a_view() -> bytes:
        """This view is for testing only."""
        return b"Done"

    ram_app.add_url_rule('/test', "test", just_a_view)
    response = ram_client.get('/test')
    assert response.status_code == 401

    ram_auth.login("user")
    response = ram_client.get('/test')
    assert response.status_code == 200
    assert response.data == b"Done"

    _make_user_inactive(ram_app, "user")
    response = ram_client.get('/test')
    assert response.status_code == 401


def test_admin_required(ram_app: GrpyApp, ram_client, ram_auth) -> None:
    """If no administrator is logged in, raise 401."""
    @admin_required
    def just_a_view() -> bytes:
        """This view is for testing only."""
        return b"Done"

    ram_app.add_url_rule('/test', "test", just_a_view)
    response = ram_client.get('/test')
    assert response.status_code == 401

    ram_auth.login("user")
    response = ram_client.get('/test')
    assert response.status_code == 403

    _make_user_inactive(ram_app, "user")
    response = ram_client.get('/test')
    assert response.status_code == 401

    ram_auth.login("admin")
    response = ram_client.get('/test')
    assert response.status_code == 200
    assert response.data == b"Done"

    _make_user_inactive(ram_app, "admin")
    response = ram_client.get('/test')
    assert response.status_code == 401


def test_login_required_redirect(ram_app: GrpyApp, ram_client, ram_auth) -> None:
    """If no user is logged in, redirect to login page."""
    @login_required_redirect
    def just_a_view() -> bytes:
        """For testing only."""
        return b"redirect"

    ram_app.add_url_rule('/test', "test", just_a_view)
    response = ram_client.get('/test')
    assert response.status_code == 302
    assert response.headers['Location'] == \
        "http://localhost" + url_for('auth.login', next_url='/test')

    ram_auth.login("user")
    response = ram_client.get('/test')
    assert response.status_code == 200
    assert response.data == b"redirect"

    _make_user_inactive(ram_app, "user")
    response = ram_client.get('/test')
    assert response.status_code == 401


def test_login_required_redirect_prefix() -> None:
    """Test redirection when there is some prefix middleware."""
    @login_required_redirect
    def just_a_view() -> bytes:
        """For testing only."""
        return b"prefix"

    grpy_app = create_app({'TESTING': True})
    grpy_app.add_url_rule('/test', "test", just_a_view)
    app = PrefixMiddleware(grpy_app, '/prefix')
    client = Client(app)
    _, status, headers = client.get('/prefix/test')  # type: ignore
    assert status.split(" ")[:1] == ["302"]
    with grpy_app.test_request_context():
        assert headers['Location'] == \
            "http://localhost/prefix" + url_for('auth.login', next_url='/prefix/test')


def test_value_or_404() -> None:
    """A non-none value will result into value, None values raise 404."""
    for value in ([1, 2, 3], [], "", 0, (1, 2, 3)):
        assert value == value_or_404(value)


def test_value_or_404_none() -> None:
    """A none value will raise 404."""
    with pytest.raises(NotFound):
        value_or_404(None)


def test_make_model() -> None:
    """A User model can be created from dict."""
    user = make_model(User, {"ident": "uid"}, {"permissions": Permissions(0)})
    assert user == User(None, "uid")


def test_update_model() -> None:
    """An User model can be updated from dict."""
    key = UserKey(int=1)
    user = update_model(User(key, "uid"), {'ident': "user", 'invalid': 1})
    assert user == User(key, "user")


def test_datetime_format(ram_app) -> None:  # pylint: disable=unused-argument
    """Return a datetime according to given format."""
    assert datetimeformat() is None
    assert datetimeformat(None, None, False) is None

    dt_val = datetime.datetime(2019, 2, 4, 16, 55, 0, tzinfo=now().tzinfo)
    assert datetimeformat(dt_val, "iso-short", False) == "2019-02-04 16:55 UTC"
    assert datetimeformat(dt_val, "YYYY", False) == "2019"
