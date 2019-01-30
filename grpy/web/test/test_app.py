
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

"""Test the web application object itself."""

import os

from flask import g

from ..app import create_app


def test_config():
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
def test_env_config(monkeypatch):
    """Test overwriting config by environments vars."""
    assert "ram:" in create_app()._repository_factory.url
    monkeypatch.setitem(os.environ, 'REPOSITORY', "invalid")
    monkeypatch.setitem(os.environ, 'TESTING', "True")
    assert "dummy:" in create_app()._repository_factory.url
# pylint: enable=protected-access
