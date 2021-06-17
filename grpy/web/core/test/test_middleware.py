##
#    Copyright (c) 2019-2021 Detlef Stern
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

"""Test the middleware."""

from flask import Flask
from werkzeug.test import Client

from ...app import create_app
from ..middleware import (PrefixMiddleware, cleanup_prefix,
                          get_prefix_middleware)


def _just_a_view() -> bytes:
    """Just a test view."""
    return b"jaw"


def _make_app() -> Flask:
    """Create an app with a test view."""
    grpy_app = create_app({'TESTING': True})
    grpy_app.add_url_rule('/test', "test", _just_a_view)
    return grpy_app


def test_cleanup_prefix() -> None:
    """A prefix has to be cleaned up."""
    assert cleanup_prefix("") == "/"
    assert cleanup_prefix("/") == "/"
    for prefix in ('prefix', '/prefix', 'prefix/', '/prefix/'):
        assert cleanup_prefix(prefix) == "/prefix"


def test_create() -> None:
    """An empty prefix will not add a middleware."""
    app = get_prefix_middleware("app", "")
    assert app == "app"
    app = get_prefix_middleware("app", "/")
    assert app == "app"
    app = get_prefix_middleware("app", "/bla")
    assert app != "app"
    assert isinstance(app, PrefixMiddleware)


def test_prefix_call_valid() -> None:
    """A valid prefix will lead to valid results."""
    app = PrefixMiddleware(_make_app(), "prefix")
    client = Client(app)
    resp = client.get('/prefix/test')
    assert resp.status.split(" ")[:1] == ['200']
    assert resp.data == b"jaw"


def test_prefix_call_invalid() -> None:
    """An invalid prefix will lead to error page."""
    app = PrefixMiddleware(_make_app(), "prefix")
    client = Client(app)
    resp = client.get('/test')
    assert resp.status.split(" ")[:1] == ['404']


def test_prefix_call_scheme() -> None:
    """Call middleware with given HTTP_X_SCHEME."""

    def wsgi_app(environ, _start_response):
        """WSGI app for testing."""
        assert environ['PATH_INFO'] == '/test'
        assert environ['SCRIPT_NAME'] == '/prefix'
        assert environ['wsgi.url_scheme'] == "http"
        assert environ['HTTP_HOST'] == "host.domain"

    app = PrefixMiddleware(wsgi_app, "prefix")
    app({
        'PATH_INFO': '/prefix/test',
        'HTTP_X_SCHEME': "http",
        'HTTP_X_FORWARDED_HOST': "host.domain"}, None)
