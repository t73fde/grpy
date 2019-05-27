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

"""Default configuration."""

import platform

# Secret key for encryption of user sessions and some other data.
# This default key should be sufficiently safe, as long the host name is not
# known to others. If you run Grpy inside a Docker container, this is mostly
# true. For additional security, please provide a sufficient long random key.
# More information: http://flask.pocoo.org/docs/1.0/config/#SECRET_KEY
SECRET_KEY = "".join(tuple(platform.uname()._asdict().values()) +
                     platform.python_build())

# Specification of the repository that stores the data. Possible values:
# * "ram://": a RAM-based repository, not useful for production; fallback
#             if everything fails.
# * "sqlite:///": a SQLite-based repository, that stores the data in memory
#             too. Not useful for production, but for debugging.
# * "sqlite:PATH": a SQLite-based repository, that stores data in a file. PATH
#             is relative to current directory, e.g. "sqlite:db/grpy.sqlite3".
# * "sqlite://PATH": a SQLite-based repository. PATH is an absolute name, must
#             start with a "/", e.g. "sqlite:///var/db/grpy.sqlite3".
REPOSITORY = "ram://"

# Level of logging. See: https://docs.python.org/3/library/logging.html#logging-levels
LOG_LEVEL = "NOTSET"

# Endpoint that provides Basic Authentication
AUTH_URL = "http://localhost:9876/"

# Specifies whether user names are case sensitive or not, e.g. whether "USER"
# and "user" are different user identifications or not.
# Per default, user names are not case sensitive
AUTH_CASE = False

# The default time zone is where you expect most of your users.
# An illegal value will result in UTC time zone.
DEFAULT_TZ = "Europe/Berlin"

# If web application is proxied by a web server, based on an URL prefix, you
# must set this variable to the prefix, e.g. "/grpy".
URL_PREFIX = "/"
