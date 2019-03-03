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

"""Entry point of web access layer for gunicorn."""

import logging

from grpy.web.app import create_app

from .prefix_middleware import PrefixMiddleware


def create_application():
    """Create a WSGI application for use with Gunicorn."""
    gunicorn_logger = logging.getLogger('gunicorn.error')
    grpy_app = create_app({
        'LOG_LEVEL': gunicorn_logger.level,
        'LOG_HANDLERS': gunicorn_logger.handlers,
    })
    return PrefixMiddleware(grpy_app, "/grpy")


app = create_application()  # pylint: disable=invalid-name
