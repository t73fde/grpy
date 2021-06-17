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

"""Authentication logic."""

import dataclasses
from typing import Optional

import requests
from flask import current_app

from ...core import utils
from ...core.models import Permissions, User
from ...repo.base import Connection
from ...repo.logic import has_user


def check_pw(app, url: Optional[str], ident: str, password: str) -> bool:
    """Check ident / password."""
    if url is None:
        return True
    if url == "":
        return False

    try:
        response = requests.head(url, auth=(ident, password))
        status_code = response.status_code
    except requests.RequestException:
        app.log_error(
            "Unable to get authentication from '%s' for '%s'", url, ident)
        status_code = 600
    return 200 <= status_code <= 299  # type: ignore


def authenticate(ident: str, password: str) -> Optional[User]:
    """Authenticate by ident and password, and return user found."""
    app = current_app
    if not app.config.get('AUTH_CASE', False):
        ident = ident.strip().lower()
    else:
        ident = ident.strip()
    url = app.config.get("AUTH_URL", "http://localhost:9876/")
    if check_pw(app, url, ident, password):
        connection: Connection = app.get_connection()  # type: ignore
        user = connection.get_user_by_ident(ident)
        if not user:
            # The first user will be an administrator
            permissions = Permissions(0) if has_user(connection) else Permissions.ADMIN
            user = connection.set_user(User(None, ident, permissions))
        if user.is_active:
            app.login(user.key)  # type: ignore
            connection.set_user(dataclasses.replace(user, last_login=utils.now()))
            return user
    return None
