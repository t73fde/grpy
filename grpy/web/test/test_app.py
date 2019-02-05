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

"""Test the web application object itself."""

import os
import unittest.mock

from flask import g

import requests

from ..app import create_app


def test_config() -> None:
    """Test the testing environment."""
    assert not create_app().testing
    app = create_app(config_mapping={'TESTING': True})
    assert app.testing
    with app.test_request_context():
        repository = app.get_repository()
        assert repository is app.get_repository()
        assert not list(repository.iter_users())
        assert not list(repository.iter_groupings())
    with app.test_request_context():
        repository = app.get_repository()
        g_repo = g.pop('repository', None)
        assert g_repo == repository


# pylint: disable=protected-access
def test_env_config(monkeypatch) -> None:
    """Test overwriting config by environments vars."""
    assert "ram:" in create_app()._repository_factory.url
    monkeypatch.setitem(os.environ, 'REPOSITORY', "invalid")
    monkeypatch.setitem(os.environ, 'TESTING', "True")
    assert "dummy:" in create_app()._repository_factory.url
# pylint: enable=protected-access


def test_check_password(app, monkeypatch) -> None:
    """Test app.check_pw."""
    assert app.authenticate("host", "1") is not None

    # Set URL to something that is non-existing
    app.config['AUTH_URL'] = "http://this.is.sparta:480/"

    def requests_head(_url, auth):  # pylint: disable=unused-argument
        """Must return a "good" status code > 300."""
        result = unittest.mock.Mock()
        result.status_code = 500
        return result

    monkeypatch.setattr(requests, 'head', requests_head)
    assert app.authenticate("user", "1") is None

    def requests_head_raise(_url, auth):
        """Must raise an RequestException."""
        raise requests.RequestException()

    monkeypatch.setattr(requests, 'head', requests_head_raise)
    assert app.authenticate("user", "1") is None
