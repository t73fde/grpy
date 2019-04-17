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

"""Test the middleware."""

from flask import Flask
from werkzeug.test import Client

from ..app import create_app
from ..middleware import PrefixMiddleware


def _just_a_view() -> bytes:
    """Just a test view."""
    return b"jaw"


def _make_app() -> Flask:
    """Create an app with a test view."""
    grpy_app = create_app({'TESTING': True})
    grpy_app.add_url_rule('/test', "test", _just_a_view)
    return grpy_app


def test_prefix_init() -> None:
    """Test the initialization method of PrefixMiddleware."""
    grpy_app = _make_app()
    for prefix in ('prefix', '/prefix', 'prefix/', '/prefix/'):
        app = PrefixMiddleware(grpy_app, prefix)
        assert app.prefix == '/prefix'


def test_prefix_call_valid() -> None:
    """A valid prefix will lead to valid results."""
    app = PrefixMiddleware(_make_app(), "prefix")
    client = Client(app)
    iter_data, status, _headers = client.get('/prefix/test')  # type: ignore
    assert status.split(" ")[:1] == ['200']
    assert list(iter_data) == [b"jaw"]


def test_prefix_call_invalid() -> None:
    """An invalid prefix will lead to error page."""
    app = PrefixMiddleware(_make_app(), "prefix")
    client = Client(app)
    _iter_data, status, _headers = client.get('/test')  # type: ignore
    assert status.split(" ")[:1] == ['404']


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
