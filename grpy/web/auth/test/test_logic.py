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

"""Tests for the auth logic."""

import unittest.mock

import requests

from ....core.models import Permissions, User
from ...app import GrpyApp
from ..logic import authenticate, check_pw


def test_check_pw(ram_app: GrpyApp, monkeypatch, caplog) -> None:
    """Test password check."""
    assert check_pw(ram_app, None, "", "") is True
    assert check_pw(ram_app, "", "", "") is False

    url = "http://example.com"

    def requests_head_ok(_url, auth):  # pylint: disable=unused-argument
        """Must return a "good" status code > 300."""
        result = unittest.mock.Mock()
        result.status_code = 200
        return result

    monkeypatch.setattr(requests, 'head', requests_head_ok)
    assert check_pw(ram_app, url, "host", "1") is True

    def requests_head(_url, auth):  # pylint: disable=unused-argument
        """Must return a "good" status code > 300."""
        result = unittest.mock.Mock()
        result.status_code = 500
        return result

    monkeypatch.setattr(requests, 'head', requests_head)
    assert check_pw(ram_app, url, "host", "1") is False

    def requests_head_raise(_url, auth):
        """Must raise an RequestException."""
        raise requests.RequestException()

    monkeypatch.setattr(requests, 'head', requests_head_raise)
    assert check_pw(ram_app, url, "user", "1") is False
    record = caplog.records[0]
    assert record.levelname == "ERROR"
    assert record.message == \
        "Unable to get authentication from 'http://example.com' for 'user'"


def test_authenticate(ram_app: GrpyApp, monkeypatch) -> None:
    """Test authentication."""
    assert ram_app.config['AUTH_CASE'] is False
    user = authenticate("user", "1")
    assert user is not None
    assert user.is_active
    assert ram_app.get_connection().get_user_by_ident("user") is not None

    # Set URL to something that is non-existing
    ram_app.config['AUTH_URL'] = "http://this.is.sparta:480/"

    def requests_head(_url, auth):  # pylint: disable=unused-argument
        """Must return a "good" status code > 300."""
        result = unittest.mock.Mock()
        result.status_code = 500
        return result

    monkeypatch.setattr(requests, 'head', requests_head)
    assert authenticate("user", "1") is None

    def requests_head_raise(_url, auth):
        """Must raise an RequestException."""
        raise requests.RequestException()

    monkeypatch.setattr(requests, 'head', requests_head_raise)
    assert authenticate("user", "1") is None


def test_authenticate_inactive(ram_app: GrpyApp) -> None:
    """An inactive user must not be authenticated."""
    ram_app.get_connection().set_user(
        User(None, "inactive", permissions=Permissions.INACTIVE))
    assert authenticate("inactive", "1") is None


def test_authenticate_case(ram_app: GrpyApp) -> None:
    """If auth is case sensitive, different cases matter."""
    assert ram_app.config['AUTH_CASE'] is False
    ident = "UsERe"
    user = authenticate(ident, "1")
    assert user is not None
    assert user.is_active
    assert ram_app.get_connection().get_user_by_ident(ident.lower()) is not None
    assert ram_app.get_connection().get_user_by_ident(ident) is None

    ram_app.config['AUTH_CASE'] = True
    ident = "hOSteR"
    host = authenticate(ident, "1")
    assert host is not None
    assert host.is_active
    assert ram_app.get_connection().get_user_by_ident(ident.lower()) is None
    assert ram_app.get_connection().get_user_by_ident(ident) is not None


def test_authenticate_spaces(ram_app: GrpyApp) -> None:
    """Spaces around a user name are not relevant."""
    assert ram_app.config['AUTH_CASE'] is False
    ident = " SpaCe "
    user = authenticate(ident, "1")
    assert user is not None
    assert user.is_active
    assert ram_app.get_connection().get_user_by_ident(ident.strip().lower()) is not None
    assert ram_app.get_connection().get_user_by_ident(ident.strip()) is None
