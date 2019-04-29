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

"""Authentication logic."""

import dataclasses
from typing import Optional

import requests
from flask import current_app

from ...core import utils
from ...core.models import User
from ...repo.base import Connection


def check_pw(app, url: Optional[str], username: str, password: str) -> bool:
    """Check username / password."""
    if url is None:
        return True
    if url == "":
        return False

    try:
        response = requests.head(url, auth=(username, password))
        status_code = response.status_code
    except requests.RequestException:
        app.log_error(
            "Unable to get authentication from '%s' for '%s'", url, username)
        status_code = 600
    return 200 <= status_code <= 299


def authenticate(username: str, password: str) -> Optional[User]:
    """Authenticate by user name and password, and return user found."""
    username = username.lower()
    app = current_app
    url = app.config.get("AUTH_URL", "http://localhost:9876/")
    if check_pw(app, url, username, password):
        connection: Connection = app.get_connection()
        user = connection.get_user_by_ident(username)
        if not user:
            user = connection.set_user(User(None, username))
        if user.is_active:
            app.login(user)
            connection.set_user(dataclasses.replace(user, last_login=utils.now()))
            return user
    return None
