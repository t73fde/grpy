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

"""Web application for grpy."""

import os
from typing import Any, Dict, Optional, cast

import requests
from flask import Flask, g, make_response, render_template, session
from flask_babel import Babel

from ..models import Permissions, User
from ..repo import create_repository
from ..repo.logic import set_grouping_new_code
from . import policies, utils, views


class GrpyApp(Flask):
    """Application object."""

    def __init__(self, import_name):
        """Initialize the application object."""
        super().__init__(import_name)
        self._repository = None
        self.babel = None

    def setup_config(self, config_mapping: Dict[str, Any] = None) -> None:
        """Create the application configuration."""
        self.config.from_pyfile("config.py")  # type: ignore
        if config_mapping:
            if config_mapping.get('TESTING', False):
                self.config.from_mapping(  # type: ignore
                    SECRET_KEY="dev",
                    REPOSITORY="ram://",
                    WTF_CSRF_ENABLED=False,
                )
            self.config.from_mapping(config_mapping)  # type: ignore
        self.config.from_envvar("GRPY_CONFIG", silent=True)  # type: ignore
        for key, value in self.config.items():
            new_value = os.environ.get(key, None)
            if new_value is None:
                continue
            if not isinstance(value, str):
                continue
            self.config[key] = new_value

    def _set_log_level(self, log_level: Any) -> None:
        """Set the log level to a specific value."""
        if log_level is None:
            return
        if isinstance(log_level, int):
            self.logger.setLevel(log_level)  # pylint: disable=no-member
            return
        if not isinstance(log_level, str):
            return
        if log_level.isdigit():
            self.logger.setLevel(int(log_level))  # pylint: disable=no-member
            return
        self.logger.setLevel(log_level.upper())  # pylint: disable=no-member

    def setup_logging(self) -> None:
        """Set-up application logging."""
        self._set_log_level(self.config.get('LOG_LEVEL'))
        log_handlers = self.config.get('LOG_HANDLERS')
        if log_handlers:
            self.logger.handlers = log_handlers

    def setup_repository(self) -> None:
        """Add a repository to the application."""
        self._repository = create_repository(self.config['REPOSITORY'])
        self.log_info("Repository URL = '" + self._repository.url + "'")
        if self._repository.url == "ram:" and not self.testing:
            populate_testdata(self._repository)

        def save_messages(response):
            """Save messages from connection into session."""
            connection = g.get('connection', None)
            if connection:
                messages = connection.get_messages()
                if messages:
                    connection_messages = session.get('connection_messages', [])
                    for message in messages:
                        self.log_error(
                            "Repository: %s (%s)", message.text, message.category,
                            exc_info=message.exception)
                        connection_messages.append((message.category, message.text))
                    session['connection_messages'] = connection_messages
            return response

        self.after_request(save_messages)

        def close_connection(_exc: BaseException = None):
            """Close the connection to the repository."""
            connection = g.pop('connection', None)
            if connection:
                connection.close(not connection.has_errors())

        self.teardown_request(close_connection)

    def get_connection(self):
        """Return an open connection, specific for this request."""
        if 'connection' not in g:
            g.connection = self._repository.create()
        return g.connection

    @staticmethod
    def clear_session() -> None:
        """Clear the session object, but not some keys."""
        keys = set(session.keys()) - {'connection_messages'}
        for key in keys:
            del session[key]

    def setup_user_handling(self):
        """Prepare application to work with user data."""

        def load_logged_in_user() -> None:
            """Set user attribute pased on session data."""
            ident = session.get('user_identifier', None)
            if ident:
                user = self.get_connection().get_user_by_ident(ident)
                if user:
                    g.user = user
                    return None
                self.clear_session()
            g.user = None
            return None

        self.before_request(load_logged_in_user)

    def setup_babel(self):
        """Prepare application to work with Babel."""
        self.babel = Babel(self, configure_jinja=True)
        self.jinja_env.filters.update(  # pylint: disable=no-member
            datetimeformat=utils.datetimeformat,
        )

    def setup_werkzeug(self):
        """Add some globals for Werkzeug."""
        self.url_map.converters['grouping'] = utils.GroupingKeyConverter

    def setup_jinja(self):
        """Add some filters / globals for Jinja2."""
        self.jinja_env.globals.update(  # pylint: disable=no-member
            get_all_messages=utils.get_all_messages,
            color=utils.colormap,
            policy_name=policies.get_policy_name,
        )

    def login(self, user: User) -> None:
        """Log in the given user."""
        self.clear_session()
        session['user_identifier'] = user.ident

    def logout(self):
        """Log out the current user."""
        self.clear_session()

    def _check_pw(self, username: str, password: str) -> bool:
        """Check username / password."""
        url = self.config.get("AUTH_URL", "http://localhost:9876/")
        if url is None:
            return True
        if url == "":
            return False

        try:
            response = requests.head(url, auth=(username, password))
            status_code = response.status_code
        except requests.RequestException:
            self.log_error(
                "Unable to get authentication from '%s' for user '%s':", url, username)
            status_code = 600
        return 200 <= status_code <= 299

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate by user name and password, and return user found."""
        username = username.lower()
        if self._check_pw(username, password):
            connection = self.get_connection()
            user = connection.get_user_by_ident(username)
            if not user:
                user = connection.set_user(User(None, username))
            self.login(user)
            return cast(User, user)
        return None

    def log_debug(self, message: str, *args, **kwargs) -> None:
        """Emit a debug message."""
        self.logger.debug(message, *args, **kwargs)  # pylint: disable=no-member

    def log_info(self, message: str, *args, **kwargs) -> None:
        """Emit a info message."""
        self.logger.info(message, *args, **kwargs)  # pylint: disable=no-member

    def log_error(self, message: str, *args, **kwargs) -> None:
        """Emit an error message."""
        self.logger.error(message, *args, **kwargs)  # pylint: disable=no-member


def create_app(config_mapping: Dict[str, Any] = None) -> Flask:
    """Create a new web application."""
    app = GrpyApp("grpy.web")
    app.setup_config(config_mapping)
    app.setup_logging()
    app.setup_repository()
    app.setup_user_handling()
    app.setup_babel()
    app.setup_werkzeug()
    app.setup_jinja()

    for code in (401, 403, 404):
        app.register_error_handler(code, handle_client_error)

    app.add_url_rule("/", "home", views.home)
    app.add_url_rule("/about", "about", views.about)
    app.add_url_rule("/login", "login", views.login, methods=('GET', 'POST'))
    app.add_url_rule("/logout", "logout", views.logout)
    app.add_url_rule(
        "/groupings/", "grouping_create", views.grouping_create,
        methods=('GET', 'POST'))
    app.add_url_rule(
        "/groupings/<grouping:grouping_key>/", "grouping_detail",
        views.grouping_detail, methods=('GET', 'POST'))
    app.add_url_rule(
        "/groupings/<grouping:grouping_key>/edit", "grouping_update",
        views.grouping_update, methods=('GET', 'POST'))
    app.add_url_rule("/<string:code>", "shortlink", views.shortlink)
    app.add_url_rule(
        "/groupings/<grouping:grouping_key>/register", "grouping_register",
        views.grouping_register, methods=('GET', 'POST'))
    app.add_url_rule(
        "/groupings/<grouping:grouping_key>/start", "grouping_start",
        views.grouping_start, methods=('GET', 'POST'))
    app.add_url_rule(
        "/groupings/<grouping:grouping_key>/remove_groups", "grouping_remove_groups",
        views.grouping_remove_groups, methods=('GET', 'POST'))
    app.log_debug("Application created.")
    return app


def handle_client_error(exc):
    """Display an error page."""
    return make_response(render_template("%d.html" % exc.code), exc.code)


def populate_testdata(repository):
    """Add some initial data for testing."""
    connection = repository.create()
    try:
        kreuz = connection.set_user(User(None, "kreuz", Permissions.HOST))
        stern = connection.set_user(User(None, "stern", Permissions.HOST))
        connection.set_user(User(None, "student"))
        connection.set_user(User(None, "xnologin"))

        from datetime import timedelta
        from ..utils import now as utils_now
        from ..models import Grouping
        now = utils_now()
        for user in (kreuz, stern):
            set_grouping_new_code(connection, Grouping(
                None, ".", "PM", user.key,
                now, now + timedelta(days=14), None,
                "RD", 7, 7, "Note: not"))
            set_grouping_new_code(connection, Grouping(
                None, ".", "SWE", user.key,
                now, now + timedelta(days=7), now + timedelta(days=14),
                "RD", 7, 7, "Was?"))
        set_grouping_new_code(connection, Grouping(
            None, ".", "PSITS", kreuz.key,
            now + timedelta(days=1), now + timedelta(days=8), None,
            "RD", 5, 3, "Nun wird es spannend"))
    finally:
        connection.close(True)
