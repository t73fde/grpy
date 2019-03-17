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

"""
A simple WSGI middleware to set a URL prefix.

Loosely based on `werkzeug.wsgi.DispatcherMiddleware` with some ideas from
<http://blog.macuyiko.com/post/2016/fixing-flask-url_for-when-behind-mod_proxy.html>.
"""


class PrefixMiddleware:  # pylint: disable=too-few-public-methods
    """Set an URL prefix for a WSGI app."""

    @staticmethod
    def cleanup_prefix(prefix: str) -> str:
        """Ensure that prefix is in sane state."""
        result = prefix.strip()
        if not result.startswith("/"):
            result = "/" + result
        if result.endswith("/"):
            result = result[:-1]
        return result

    def __init__(self, app, prefix: str) -> None:
        """Remember the WSGI app and the prefix."""
        self.app = app
        self.prefix = self.cleanup_prefix(prefix)

    def __call__(self, environ, start_response):
        """Execute the WSGI call."""
        script = environ.get("PATH_INFO", "")
        if script.startswith(self.prefix):
            environ["SCRIPT_NAME"] = environ.get('SCRIPT_NAME', "") + self.prefix
            environ["PATH_INFO"] = script[len(self.prefix):]
            scheme = environ.get('HTTP_X_SCHEME', '')
            if scheme:
                environ['wsgi.url_scheme'] = scheme
            host = environ.get('HTTP_X_FORWARDED_HOST', '')
            if host:
                environ['HTTP_HOST'] = host
            return self.app(environ, start_response)

        message = b"Not found: you did not specify the needed URL prefix."
        response_headers = [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(message))),
        ]
        start_response('404 NOT FOUND', response_headers)
        return [message]
