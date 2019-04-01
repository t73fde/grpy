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

"""Test the web application object itself."""

import logging
import os
import unittest.mock

import requests
from flask import g, url_for
from werkzeug.test import Client

from ...repo.proxies.check import ValidatingProxyConnection
from ..app import create_app


def test_config() -> None:
    """Test the testing environment."""
    assert not create_app().testing
    app = create_app(config_mapping={'TESTING': True})
    assert app.testing
    with app.test_request_context():
        connection = app.get_connection()
        assert connection is app.get_connection()
        assert not list(connection.iter_users())
        assert not list(connection.iter_groupings())
    with app.test_request_context():
        connection = app.get_connection()
        g_connection = g.pop('connection', None)
        assert g_connection == connection


# pylint: disable=protected-access
def test_env_config(monkeypatch) -> None:
    """Test overwriting config by environments vars."""
    assert "ram:" in create_app()._repository.url
    monkeypatch.setitem(os.environ, 'REPOSITORY', "invalid")
    monkeypatch.setitem(os.environ, 'TESTING', "True")
    assert "dummy:" in create_app()._repository.url
# pylint: enable=protected-access


def _check_log_level(log_level, expected: int) -> None:
    """Check that log level was set."""
    app = create_app({'LOG_LEVEL': log_level})
    assert app.logger.level == expected  # pylint: disable=no-member


def test_setup_logging() -> None:
    """Test the various ways to setup logging."""
    assert create_app().logger.level == 0  # pylint: disable=no-member
    _check_log_level(None, 0)
    _check_log_level([], 0)
    _check_log_level(7, 7)
    _check_log_level("99", 99)
    _check_log_level("INFO", logging.INFO)

    assert create_app().logger.handlers == []
    handlers = [logging.NullHandler()]
    assert create_app({'LOG_HANDLERS': handlers}).logger.handlers == handlers


def test_check_password(app, monkeypatch) -> None:
    """Test app.check_pw."""
    assert app.authenticate("host", "1") is not None

    # Set URL to something that is non-existing
    app.config['AUTH_URL'] = "http://this.is.sparta:480/"

    def requests_head(_url, auth):  # pylint: disable=unused-argument
        """Must return a "good" status code > 300."""
        result = unittest.mock.Mock()
        result.status_code = 500
        return result

    monkeypatch.setattr(requests, 'head', requests_head)
    assert app.authenticate("user", "1") is None

    def requests_head_raise(_url, auth):
        """Must raise an RequestException."""
        raise requests.RequestException()

    monkeypatch.setattr(requests, 'head', requests_head_raise)
    assert app.authenticate("user", "1") is None


def create_grpy_app():
    """Create a new Grpy app with SQLite repository."""
    return create_app(
        config_mapping={
            'TESTING': True,
            'AUTH_URL': None,
            'REPOSITORY': "sqlite:",
        })


def do_login(grpy_app):
    """Login user 'host'."""
    client = Client(grpy_app)
    with grpy_app.test_request_context():
        _iter_data, status, headers = client.post(
            url_for('login'), data={'username': "host", 'password': "1"})
    assert status == "302 FOUND"
    assert headers['Location'] == "http://localhost/"
    return client


def test_flash_connection_messages_get(monkeypatch) -> None:
    """Ensure that messages of connection are shown as a flash message."""

    def raise_value_error(*args, **kwargs):
        """Raise a ValueError."""
        raise ValueError("Test for critical get message")

    grpy_app = create_grpy_app()
    client = do_login(grpy_app)
    monkeypatch.setattr(
        ValidatingProxyConnection, 'iter_groups_by_user', raise_value_error)
    with grpy_app.test_request_context():
        iter_data, status, _headers = client.get(url_for('home'))
    assert status == "200 OK"
    data = b" ".join(iter_data)
    assert b"builtins.ValueError: Test for critical get message" in data


def test_flash_connection_messages_push(monkeypatch) -> None:
    """Ensure that messages of connection are shown as a flash message."""

    def raise_value_error(*args, **kwargs):
        """Raise a ValueError."""
        raise ValueError("Test for critical post message")

    grpy_app = create_grpy_app()
    monkeypatch.setattr(ValidatingProxyConnection, 'set_user', raise_value_error)
    client = do_login(grpy_app)
    with grpy_app.test_request_context():
        iter_data, status, _headers = client.get(url_for('home'))
    assert status == "200 OK"
    data = b" ".join(iter_data)
    assert b"builtins.ValueError: Test for critical post message" in data
