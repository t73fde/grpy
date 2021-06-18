##
#    Copyright (c) 2018-2021 Detlef Stern
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

import pytest
import pytz.tzinfo  # type: ignore
from flask import Flask, g, url_for
from werkzeug.test import Client

from ...repo.proxies.check import ValidatingProxyConnection
from ..app import GrpyApp, create_app


def test_grpy_app() -> None:
    """Some simple tests with a partially set-up class."""
    app = GrpyApp("grpy.app")
    with app.test_request_context():
        with pytest.raises(TypeError, match="Repository not set"):
            assert app.get_connection()


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
    app = create_app()
    assert app._repository is not None
    assert "ram:" in app._repository.url
    assert not app.testing
    assert app.config['AUTH_CASE'] is False

    monkeypatch.setitem(os.environ, 'REPOSITORY', "invalid")
    monkeypatch.setitem(os.environ, 'TESTING', "True")
    monkeypatch.setitem(os.environ, 'AUTH_CASE', "Yes")
    monkeypatch.setitem(os.environ, 'ANY_NUM', "17")
    app = create_app(config_mapping={'ANY_NUM': 3})
    assert app._repository is not None
    assert "dummy:" in app._repository.url
    assert app.testing
    assert app.config['AUTH_CASE'] is True
    assert app.config['ANY_NUM'] == 3
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


def test_setup_time_zone() -> None:
    """After app creation, there is a valid timezone."""
    assert isinstance(create_app().default_tz, pytz.tzinfo.BaseTzInfo)


def test_setup_time_zone_invalid(caplog) -> None:
    """When specifying an invalid time zone. use UTC and log an error."""
    assert create_app(config_mapping={'DEFAULT_TZ': "*none*"}).default_tz is pytz.UTC
    assert caplog.record_tuples == [
        ('grpy.web', logging.ERROR, "Unknown DEFAULT_TZ: '*none*', will use 'UTC'."),
    ]


def create_grpy_app() -> Flask:
    """Create a new Grpy app with SQLite repository."""
    return create_app(
        config_mapping={
            'TESTING': True,
            'AUTH_URL': None,
            'REPOSITORY': "sqlite:",
        })


def do_login(grpy_app: Flask) -> Client:
    """Login user 'host'."""
    client = Client(grpy_app)
    with grpy_app.test_request_context():
        resp = client.post(
            url_for('auth.login'), data={'ident': "host", 'password': "1"})
    assert resp.status == "302 FOUND"
    assert resp.headers['Location'] == "http://localhost/"
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
        resp = client.get(url_for('home'))
    assert resp.status == "200 OK"
    assert b"builtins.ValueError: Test for critical get message" in resp.data


def test_flash_connection_messages_push(monkeypatch) -> None:
    """Ensure that messages of connection are shown as a flash message."""

    def raise_value_error(*args, **kwargs):
        """Raise a ValueError."""
        raise ValueError("Test for critical post message")

    grpy_app = create_grpy_app()
    monkeypatch.setattr(ValidatingProxyConnection, 'set_user', raise_value_error)
    client = do_login(grpy_app)
    with grpy_app.test_request_context():
        resp = client.get(url_for('home'))
    assert resp.status == "200 OK"
    assert b"builtins.ValueError: Test for critical post message" in resp.data
