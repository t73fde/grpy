
##
#    Copyright (c) 2018 Detlef Stern
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
from typing import Any, Dict

from flask import Flask, g, session

from flask_babel import Babel

from grpy.models import Permission, User
from grpy.repo import create_factory
from grpy.repo.logic import set_grouping_new_code

from . import utils, views


class GrpyApp(Flask):
    """Application object."""

    def __init__(self, import_name):
        """Initialize the application object."""
        super().__init__(import_name)
        self._repository_factory = None
        self.babel = None

    def setup_config(self, config_mapping: Dict[str, Any] = None) -> None:
        """Create the application configuration."""
        if config_mapping:
            self.config.from_mapping(
                SECRET_KEY="dev",
                REPOSITORY="ram://",
                WTF_CSRF_ENABLED=False,
            )
            self.config.from_mapping(config_mapping)
        else:
            self.config.from_pyfile("config.py")
            self.config.from_envvar("GRPY_CONFIG", silent=True)
        for key, value in self.config.items():
            new_value = os.environ.get(key, None)
            if new_value is None:
                continue
            if not isinstance(value, str):
                continue
            self.config[key] = new_value

    def setup_repository(self):
        """Add a repository to the application."""
        self._repository_factory = create_factory(self.config['REPOSITORY'])
        if self._repository_factory.url == "ram:" and not self.testing:
            populate_testdata(self._repository_factory)

        def close_repository(_exc: BaseException = None):
            """Close the repository."""
            repository = g.pop('repository', None)
            if repository:
                repository.close()

        self.teardown_request(close_repository)

    def get_repository(self):
        """Return an open repository, specific for this request."""
        if 'repository' not in g:
            g.repository = self._repository_factory.create()
        return g.repository

    def setup_user_handling(self):
        """Prepare application to work with user data."""

        def load_logged_in_user() -> None:
            """Set user attribute pased on session data."""
            username = session.get('username', None)
            if username:
                user = self.get_repository().get_user_by_username(username)
                if user:
                    g.user = user
                    return None
                session.clear()
            g.user = None
            return None

        self.before_request(load_logged_in_user)

    def setup_babel(self):
        """Prepare application to work with Babel."""
        self.babel = Babel(self, configure_jinja=True)
        self.jinja_env.filters.update(  # pylint: disable=no-member
            datetimeformat=utils.datetimeformat,
        )

    def setup_jinja(self):
        """Add some filters / globals for Jinja2."""
        self.jinja_env.globals.update(  # pylint: disable=no-member
            color=utils.colormap,
        )

    @staticmethod
    def login(user: User) -> None:
        """Log in the given user."""
        session.clear()
        session['username'] = user.username

    @staticmethod
    def logout():
        """Log out the current user."""
        session.clear()

    def log_debug(self, message: str, *args, **kwargs) -> None:
        """Emit a debug message."""
        self.logger.debug(message, *args, **kwargs)  # pylint: disable=no-member


def create_app(config_mapping: Dict[str, Any] = None) -> Flask:
    """Create a new web application."""
    app = GrpyApp("grpy.web")
    app.setup_config(config_mapping)
    app.setup_repository()
    app.setup_user_handling()
    app.setup_babel()
    app.setup_jinja()

    app.add_url_rule("/", "home", views.home)
    app.add_url_rule("/about", "about", views.about)
    app.add_url_rule("/login", "login", views.login, methods=('GET', 'POST'))
    app.add_url_rule("/logout", "logout", views.logout)
    app.add_url_rule(
        "/groupings/", "grouping_create", views.grouping_create,
        methods=('GET', 'POST'))
    app.add_url_rule(
        "/groupings/<uuid:key>/", "grouping_detail", views.grouping_detail)
    app.add_url_rule(
        "/groupings/<uuid:key>/edit", "grouping_update", views.grouping_update,
        methods=('GET', 'POST'))
    app.add_url_rule("/<string:code>/", "shortlink", views.shortlink)
    app.add_url_rule(
        "/groupings/<uuid:key>/register", "grouping_register", views.grouping_register,
        methods=('GET', 'POST'))
    app.log_debug("Application created.")
    return app


def populate_testdata(repository_factory):
    """Add some initial data for testing."""
    repository = repository_factory.create()
    try:
        kreuz = repository.set_user(User(None, "kreuz", Permission.HOST))
        stern = repository.set_user(User(None, "stern", Permission.HOST))
        repository.set_user(User(None, "student"))
        repository.set_user(User(None, "xnologin"))

        from datetime import timedelta
        from ..utils import now as utils_now
        from ..models import Grouping
        now = utils_now()
        for user in (kreuz, stern):
            set_grouping_new_code(repository, Grouping(
                None, ".", "PM", user.key,
                now, now + timedelta(days=14), None,
                "RD", 7, 7, "Note: not"))
            set_grouping_new_code(repository, Grouping(
                None, ".", "SWE", user.key,
                now, now + timedelta(days=7), now + timedelta(days=14),
                "RD", 7, 7, "Was?"))
        set_grouping_new_code(repository, Grouping(
            None, ".", "PSITS", kreuz.key,
            now + timedelta(days=1), now + timedelta(days=8), None,
            "RD", 5, 3, "Nun wird es spannend"))
    finally:
        repository.close()
