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

"""Web application for grpy."""

import functools
import os
from typing import Any, Dict, Optional, cast

import pytz
import pytz.exceptions  # type: ignore
import pytz.tzinfo  # type: ignore
from flask import Flask, g, make_response, render_template, session
from flask_babel import Babel  # type: ignore

from ..core.models import Permissions, User, UserKey
from ..repo import create_repository
from ..repo.base import Connection, Repository
from ..repo.logic import set_grouping_new_code
from ..version import Version, get_version, read_version_file
from . import auth, grouping, policies, user
from .core import utils, views
from .core.middleware import get_prefix_middleware


class GrpyApp(Flask):
    """Application object."""

    def __init__(self, import_name: str):
        """Initialize the application object."""
        super().__init__(import_name)
        self._repository: Optional[Repository] = None
        self.version: Optional[Version] = None
        self.babel = None
        self.default_tz: pytz.tzinfo.BaseTzInfo = pytz.UTC

    def setup_config(self, config_mapping: Dict[str, Any] = None) -> None:
        """Create the application configuration."""
        self.config.from_pyfile("config.py")
        if config_mapping:
            if config_mapping.get('TESTING', False):
                self.config.from_mapping(  # nosec, type: ignore
                    SECRET_KEY="dev",
                    REPOSITORY="ram://",
                    WTF_CSRF_ENABLED=False,
                )
            self.config.from_mapping(config_mapping)
        self.config.from_envvar("GRPY_CONFIG", silent=True)
        for key, value in self.config.items():
            new_value = os.environ.get(key, None)
            if new_value is None:
                continue
            if isinstance(value, str):
                self.config[key] = new_value
            elif isinstance(value, bool):
                self.config[key] = utils.to_bool(new_value)

        # Ensure that specific values are of specific types
        self.config['AUTH_CASE'] = utils.to_bool(self.config.get('AUTH_CASE', None))

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

    def _setup_logging(self) -> None:
        """Set application logging up."""
        self._set_log_level(self.config.get('LOG_LEVEL'))
        log_handlers = self.config.get('LOG_HANDLERS')
        if log_handlers:
            self.logger.handlers = log_handlers

    def _setup_version(self) -> None:
        """Provide version information."""
        self.version = get_version(read_version_file(self.root_path, 3))

    def _setup_time_zone(self) -> None:
        """Determine the applications default time zone."""
        tz_name = self.config.get('DEFAULT_TZ', "UTC")
        try:
            self.default_tz = pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            self.log_error(f"Unknown DEFAULT_TZ: '{tz_name}', will use 'UTC'.")
            self.default_tz = pytz.UTC

    def _setup_repository(self) -> None:
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

    def get_connection(self) -> Connection:
        """Return an open connection, specific for this request."""
        if 'connection' not in g:
            if self._repository is None:
                raise TypeError("Repository not set")
            g.connection = \
                self._repository.create()  # pylint: disable=assigning-non-slot
        return cast(Connection, g.connection)

    @staticmethod
    def _clear_session() -> None:
        """Clear the session object, but not some keys."""
        keys = set(session.keys()) - {'connection_messages'}
        for key in keys:
            del session[key]

    def _setup_user_handling(self) -> None:
        """Prepare application to work with user data."""

        def load_logged_in_user() -> None:
            """Set user attribute pased on session data."""
            user_key_int = session.get('user', None)
            if user_key_int:
                user_obj = self.get_connection().get_user(UserKey(int=user_key_int))
                if user_obj:
                    g.user = user_obj  # pylint: disable=assigning-non-slot
                    return None
                self._clear_session()
            g.user = None  # pylint: disable=assigning-non-slot
            return None

        self.before_request(load_logged_in_user)

    def _setup_babel(self) -> None:
        """Prepare application to work with Babel."""
        self.babel = Babel(self, configure_jinja=True)

    def _setup_werkzeug(self) -> None:
        """Add some globals for Werkzeug."""
        self.url_map.converters['grouping'] = utils.GroupingKeyConverter
        self.url_map.converters['user'] = utils.UserKeyConverter

    def _setup_jinja(self) -> None:
        """Add some filters / globals for Jinja2."""
        self.jinja_env.filters.update(  # pylint: disable=no-member
            datetimeformat=utils.datetimeformat,
            truncate_ident=functools.partial(utils.truncate, 20),
            truncate_gname=functools.partial(utils.truncate, 30),
        )
        self.jinja_env.globals.update(  # pylint: disable=no-member
            get_all_messages=utils.get_all_messages,
            color=utils.colormap,
            policy_name=policies.get_policy_name,
        )

    def login(self, user_key: UserKey) -> None:
        """Log in the given user."""
        self._clear_session()
        session['user'] = user_key.int

    def logout(self):
        """Log out the current user."""
        self._clear_session()

    def log_debug(self, message: str, *args, **kwargs) -> None:
        """Emit a debug message."""
        self.logger.debug(message, *args, **kwargs)  # pylint: disable=no-member

    def log_info(self, message: str, *args, **kwargs) -> None:
        """Emit a info message."""
        self.logger.info(message, *args, **kwargs)  # pylint: disable=no-member

    def log_error(self, message: str, *args, **kwargs) -> None:
        """Emit an error message."""
        self.logger.error(message, *args, **kwargs)  # pylint: disable=no-member

    def setup(self) -> None:
        """Set the app up."""
        self._setup_logging()
        self._setup_version()
        self._setup_time_zone()
        self._setup_repository()
        self._setup_user_handling()
        self._setup_babel()
        self._setup_werkzeug()
        self._setup_jinja()


def create_app(config_mapping: Dict[str, Any] = None) -> GrpyApp:
    """Create a new web application."""
    app = GrpyApp("grpy.web")
    app.setup_config(config_mapping)
    app.setup()
    version = cast(Version, app.version)
    app.log_info(
        f"Version = {version.user_version} / "
        f"{version.vcs_version} / {version.build_date}")

    for code in (401, 403, 404):
        app.register_error_handler(code, handle_client_error)

    app.add_url_rule("/", "home", views.home)
    app.add_url_rule("/about", "about", views.about)
    app.add_url_rule("/<string:code>", "shortlink", views.shortlink)

    auth_blueprint = auth.create_blueprint()
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    grouping_blueprint = grouping.create_blueprint()
    app.register_blueprint(grouping_blueprint, url_prefix='/groupings')

    user_blueprint = user.create_blueprint()
    app.register_blueprint(user_blueprint, url_prefix='/users')

    url_prefix = app.config.get("URL_PREFIX", "/")
    app.wsgi_app = get_prefix_middleware(app.wsgi_app, url_prefix)  # type: ignore
    app.log_debug("Application created.")
    return app


def handle_client_error(exc):
    """Display an error page."""
    return make_response(render_template("%d.html" % exc.code), exc.code)


def populate_testdata(repository: Repository) -> None:
    """Add some initial data for testing."""
    connection = repository.create()
    try:
        kreuz = connection.set_user(User(
            None, "kreuz", Permissions.HOST | Permissions.ADMIN))
        stern = connection.set_user(User(None, "stern", Permissions.HOST))
        connection.set_user(User(None, "student"))
        connection.set_user(User(None, "xnologin"))

        from datetime import (  # pylint: disable=import-outside-toplevel
            timedelta)
        from ..core.models import (  # pylint: disable=import-outside-toplevel
            Grouping)
        from ..core.utils import (  # pylint: disable=import-outside-toplevel
            now as utils_now)

        now = utils_now()
        for user_obj in (kreuz, stern):
            set_grouping_new_code(connection, Grouping(
                None, ".", "PM", cast(UserKey, user_obj.key),
                now, now + timedelta(days=14), None,
                "RD", 7, 7, "Note: not"))
            set_grouping_new_code(connection, Grouping(
                None, ".", "SWE", cast(UserKey, user_obj.key),
                now, now + timedelta(days=7), now + timedelta(days=14),
                "RD", 7, 7, "Was?"))
        set_grouping_new_code(connection, Grouping(
            None, ".", "PSITS", cast(UserKey, kreuz.key),
            now + timedelta(days=1), now + timedelta(days=8), None,
            "RD", 5, 3, "Nun wird es spannend"))
    finally:
        connection.close(True)
