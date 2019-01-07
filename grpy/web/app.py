
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

from typing import Any, Dict

from flask import Flask, g, session

from grpy.models import Permission, User
from grpy.repo import create_factory

from . import views


class GrpyApp(Flask):
    """Application object."""

    def __init__(self, import_name):
        """Initialize the application object."""
        super().__init__(import_name)
        self._repository_factory = None

    def setup_config(self, config_mapping: Dict[str, Any] = None) -> None:
        """Create the application configuration."""
        if config_mapping:
            self.config.from_mapping(
                SECRET_KEY="dev",
                REPOSITORY="ram://",
            )
            self.config.from_mapping(config_mapping)
        else:
            self.config.from_pyfile("config.py")
            self.config.from_envvar("GRPY_CONFIG", silent=True)

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

    app.add_url_rule("/", "home", views.home)
    app.add_url_rule("/about", "about", views.about)
    app.add_url_rule("/login", "login", views.login, methods=('GET', 'POST'))
    app.add_url_rule("/logout", "logout", views.logout)
    app.add_url_rule("/groupings/<uuid:key>/", "grouping_detail", views.grouping_detail)
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
        from .. import utils
        from ..models import Grouping
        now = utils.now()
        for user in (kreuz, stern):
            repository.set_grouping(Grouping(
                None, "PM", user.key,
                now, now + timedelta(days=14), None,
                "RD", 7, 7, "Note: not"))
            repository.set_grouping(Grouping(
                None, "SWE", user.key,
                now, now + timedelta(days=7), now + timedelta(days=14),
                "RD", 7, 7, "Was?"))
        repository.set_grouping(Grouping(
            None, "PSITS", kreuz.key,
            now + timedelta(days=1), now + timedelta(days=8), None,
            "RD", 5, 3, "Nun wird es spannend"))
    finally:
        repository.close()