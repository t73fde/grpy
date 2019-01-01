
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

"""Test the repositories."""

import uuid

import pytest

import grpy  # noqa: I100

from .. import create_factory
from ..base import DuplicateKey, Repository

# pylint: disable=redefined-outer-name


@pytest.fixture(params=["ram"])
def repository(request):
    """Provide an open repository."""
    factory = create_factory(request.param)
    repo = factory.create()
    yield repo
    factory.close(repo)


def test_insert_user(repository: Repository):
    """Check that inserting a new user works."""
    user = grpy.User(None, "user", True)
    new_user = repository.set_user(user)
    assert not user.key
    assert new_user.key
    assert new_user.username == user.username
    assert new_user.is_host == user.is_host

    with pytest.raises(DuplicateKey):
        repository.set_user(user)


def test_update_user(repository: Repository):
    """Check that updating an existing user works."""
    user = grpy.User(uuid.uuid4(), "user", True)
    with pytest.raises(ValueError):
        repository.set_user(user)

    user = repository.set_user(grpy.User(None, "user", True))
    new_user = user._replace(is_host=False)
    assert user.key == new_user.key
    newer_user = repository.set_user(new_user)
    assert new_user == newer_user

    user_2 = repository.set_user(grpy.User(None, "user_2", False))
    renamed_user = user_2._replace(username=user.username)
    with pytest.raises(DuplicateKey):
        repository.set_user(renamed_user)


def test_get_user(repository: Repository):
    """An inserted or updated user can be retrieved."""
    user = repository.set_user(grpy.User(None, "user", True))
    new_user = repository.get_user(user.key)
    assert new_user == user

    newer_user = user._replace(is_host=not user.is_host)
    repository.set_user(newer_user)
    last_user = repository.get_user(user.key)
    assert last_user.is_host != user.is_host

    for key in (None, "", 0, uuid.uuid4()):
        not_found = repository.get_user(key)
        assert not_found is None


def test_get_user_by_username(repository: Repository):
    """Retrieve an user by its username."""
    user = repository.set_user(grpy.User(None, "user", True))
    new_user = repository.get_user_by_username(user.username)
    assert new_user == user

    newer_user = user._replace(is_host=not user.is_host)
    repository.set_user(newer_user)
    last_user = repository.get_user_by_username(user.username)
    assert last_user.is_host != user.is_host

    for username in (None, "", "invalid"):
        not_found = repository.get_user_by_username(username)
        assert not_found is None
