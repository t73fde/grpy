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

import datetime
import random
import uuid
from typing import List

import pytest

from .. import create_factory
from ..base import DuplicateKey, NothingToUpdate, Repository
from ..ram import RamRepositoryFactory
from ... import utils
from ...models import Grouping, Permission, Registration, User

# pylint: disable=redefined-outer-name


def test_wrong_repository_url():
    """If an illegal URL ist given, a dummy factory must be returned."""
    factory = create_factory(None)
    assert factory.url == "dummy:"


def test_no_connection(monkeypatch):
    """If unable to connect to data store, a dummy factory must be returned."""
    def return_false(_):
        return False
    monkeypatch.setattr(RamRepositoryFactory, "can_connect", return_false)
    factory = create_factory("ram:")
    assert factory.url == "dummy:"


def test_insert_user(repository: Repository):
    """Check that inserting a new user works."""
    user = User(None, "user", Permission.HOST)
    new_user = repository.set_user(user)
    assert not user.key
    assert new_user.key
    assert new_user.username == user.username
    assert new_user.is_host == user.is_host

    with pytest.raises(DuplicateKey):
        repository.set_user(user)


def test_update_user(repository: Repository):
    """Check that updating an existing user works."""
    user = User(uuid.uuid4(), "user", True)
    with pytest.raises(NothingToUpdate):
        repository.set_user(user)

    user = repository.set_user(User(None, "user", Permission.HOST))
    new_user = user._replace(permission=Permission(0))
    assert user.key == new_user.key
    newer_user = repository.set_user(new_user)
    assert new_user == newer_user

    user_2 = repository.set_user(User(None, "user_2"))
    renamed_user = user_2._replace(username=user.username)
    with pytest.raises(DuplicateKey):
        repository.set_user(renamed_user)


def test_get_user(repository: Repository):
    """An inserted or updated user can be retrieved."""
    user = repository.set_user(User(None, "user", Permission.HOST))
    new_user = repository.get_user(user.key)
    assert new_user == user

    newer_user = user._replace(permission=Permission(0))
    repository.set_user(newer_user)
    last_user = repository.get_user(user.key)
    assert last_user.is_host != user.is_host

    for key in (None, "", 0, uuid.uuid4()):
        not_found = repository.get_user(key)
        assert not_found is None


def test_get_user_by_username(repository: Repository):
    """Retrieve an user by its username."""
    user = repository.set_user(User(None, "user", Permission.HOST))
    new_user = repository.get_user_by_username(user.username)
    assert new_user == user

    newer_user = user._replace(permission=Permission(0))
    repository.set_user(newer_user)
    last_user = repository.get_user_by_username(user.username)
    assert last_user.is_host != user.is_host

    for username in (None, "", "invalid"):
        not_found = repository.get_user_by_username(username)
        assert not_found is None


def test_get_user_by_username_after_change(repository: Repository):
    """After a change to an username, the old name must not be accessible."""
    username = "user"
    repository.set_user(User(None, username, True))
    user = repository.get_user_by_username(username)
    user = user._replace(username="resu")
    repository.set_user(user)
    assert repository.get_user_by_username(username) is None


def setup_users(repository: Repository, count: int) -> List[User]:
    """Insert some users into repository."""
    result = []
    is_host = False
    for i in range(count):
        user = repository.set_user(User(None, "user-%d" % i, is_host))
        result.append(user)
        is_host = not is_host
    return result


def test_iter_users(repository: Repository) -> None:
    """List all users."""
    all_users = setup_users(repository, 17)
    iter_users = list(repository.iter_users())
    assert len(iter_users) == len(all_users)
    assert set(iter_users) == set(all_users)


def test_iter_users_where(repository: Repository) -> None:
    """Select some user from list of all users."""
    all_users = setup_users(repository, 13)
    users = list(repository.iter_users(where={'permission__eq': Permission.HOST}))
    non_users = list(repository.iter_users(where={'permission__ne': Permission.HOST}))
    assert len(users) + len(non_users) == len(all_users)
    assert set(users + non_users) == set(all_users)

    for field_name in User._fields:
        where = {field_name + "__eq": None}
        users = list(repository.iter_users(where=where))
        assert users == []
        where = {field_name + "__ne": None}
        users = list(repository.iter_users(where=where))
        assert set(users) == set(all_users)

    for _ in range(len(all_users)):
        user = random.choice(all_users)
        users = list(repository.iter_users(where={'username__eq': user.username}))
        assert len(users) == 1
        assert users[0] == user

        other_users = list(repository.iter_users(where={'username__ne': user.username}))
        assert len(other_users) + 1 == len(all_users)
        assert set(other_users + users) == set(all_users)

        users = list(repository.iter_users(where={'username__lt': user.username}))
        non_users = list(repository.iter_users(where={'username__ge': user.username}))
        assert len(users) + len(non_users) == len(all_users)
        assert set(users + non_users) == set(all_users)

        users = list(repository.iter_users(where={'username__gt': user.username}))
        non_users = list(repository.iter_users(where={'username__le': user.username}))
        assert len(users) + len(non_users) == len(all_users)
        assert set(users + non_users) == set(all_users)

        no_users = list(repository.iter_users(where={'key__eq': uuid.uuid4()}))
        assert no_users == []


def test_iter_users_order(repository: Repository) -> None:
    """Order the list of users."""
    all_users = setup_users(repository, 7)  # Must be less than 10
    users = list(repository.iter_users(order=["username"]))
    assert users == all_users
    users = list(repository.iter_users(order=["+username"]))
    assert users == all_users
    users = list(repository.iter_users(order=["-username"]))
    assert users == list(reversed(all_users))


def create_grouping(repository: Repository) -> Grouping:
    """Create a new grouping."""
    users = repository.iter_users(where={'username__eq': 'user'})
    if not users:
        user = repository.set_user(User(None, "user", Permission.HOST))
    else:
        user = list(users)[0]

    now = utils.now()
    return Grouping(
        None, "code", "grouping", user.key,
        now, now + datetime.timedelta(days=7), None,
        "RD", 7, 7, "Note")


def test_insert_grouping(repository: Repository):
    """Check that inserting a new grouping works."""
    grouping = create_grouping(repository)
    new_grouping = repository.set_grouping(grouping)
    assert not grouping.key
    assert new_grouping.key
    assert new_grouping.code == grouping.code
    assert new_grouping.name == grouping.name
    assert new_grouping.host == grouping.host
    assert new_grouping.begin_date == grouping.begin_date
    assert new_grouping.final_date == grouping.final_date
    assert new_grouping.close_date == grouping.close_date
    assert new_grouping.strategy == grouping.strategy
    assert new_grouping.max_group_size == grouping.max_group_size
    assert new_grouping.member_reserve == grouping.member_reserve
    assert new_grouping.note == grouping.note

    with pytest.raises(DuplicateKey):
        repository.set_grouping(grouping)


def test_update_grouping(repository: Repository):
    """Check that updating an existing grouping works."""
    grouping = create_grouping(repository)
    grouping = grouping._replace(key=uuid.uuid4())
    with pytest.raises(NothingToUpdate):
        repository.set_grouping(grouping)

    grouping = repository.set_grouping(create_grouping(repository))
    new_grouping = grouping._replace(name="new name")
    assert grouping.key == new_grouping.key
    newer_grouping = repository.set_grouping(new_grouping)
    assert new_grouping == newer_grouping


def test_get_grouping(repository: Repository):
    """An inserted or updated grouping can be retrieved."""
    grouping = repository.set_grouping(create_grouping(repository))
    new_grouping = repository.get_grouping(grouping.key)
    assert new_grouping == grouping

    newer_grouping = grouping._replace(name="new name")
    repository.set_grouping(newer_grouping)
    last_grouping = repository.get_grouping(grouping.key)
    assert last_grouping.name != grouping.name

    for key in (None, "", 0, uuid.uuid4()):
        not_found = repository.get_grouping(key)
        assert not_found is None


def test_get_grouping_by_code(repository: Repository):
    """An inserted or updated grouping can be retrieved by short code."""
    grouping = repository.set_grouping(create_grouping(repository))
    new_grouping = repository.get_grouping_by_code(grouping.code)
    assert new_grouping == grouping

    newer_grouping = grouping._replace(name="new name")
    repository.set_grouping(newer_grouping)
    last_grouping = repository.get_grouping(grouping.key)
    assert last_grouping.name != grouping.name

    for username in (None, "", "invalid"):
        not_found = repository.get_user_by_username(username)
        assert not_found is None


def test_get_grouping_by_code_after_change(repository: Repository):
    """After a change to a code, the old code must not be accessible."""
    grouping = repository.set_grouping(create_grouping(repository))
    repository.set_grouping(grouping._replace(code="0000"))
    assert repository.get_grouping_by_code(grouping.code) is None


def setup_groupings(repository: Repository, count: int) -> List[Grouping]:
    """Insert some groupings into repository."""
    hosts = [
        repository.set_user(User(None, "host-1", True)),
        repository.set_user(User(None, "host-2", True)),
    ]
    now = utils.now()
    timedelta = datetime.timedelta
    days = 0
    result = []
    for i in range(count):
        grouping = repository.set_grouping(Grouping(
            None, "cd%d" % i, "grouping-%d" % i, hosts[days % len(hosts)].key,
            now + timedelta(days=days), now + timedelta(days=days + 7), None,
            "RD", days + 1, 5, "Note %d" % i))
        result.append(grouping)
        days += 1
    return result


def test_iter_groupings(repository: Repository) -> None:
    """List all groupings."""
    all_groupings = setup_groupings(repository, 17)
    iter_groupings = list(repository.iter_groupings())
    assert len(iter_groupings) == len(all_groupings)
    assert set(iter_groupings) == set(all_groupings)


def test_iter_groupings_where(repository: Repository) -> None:
    """Select some grouping from list of all groupings."""
    all_groupings = setup_groupings(repository, 13)
    groupings = list(repository.iter_groupings(where={'close_date__eq': None}))
    non_groupings = list(repository.iter_groupings(where={'close_date__ne': None}))
    assert len(groupings) + len(non_groupings) == len(all_groupings)
    assert set(groupings + non_groupings) == set(all_groupings)

    for _ in range(len(all_groupings)):
        grouping = random.choice(all_groupings)
        groupings = list(repository.iter_groupings(where={'name__eq': grouping.name}))
        assert len(groupings) == 1
        assert groupings[0] == grouping

        other_groupings = list(
            repository.iter_groupings(where={'name__ne': grouping.name}))
        assert len(other_groupings) + 1 == len(all_groupings)
        assert set(other_groupings + groupings) == set(all_groupings)

        groupings = list(repository.iter_groupings(where={
            'close_date__lt': None, 'close_date__ne': None}))
        non_groupings = list(repository.iter_groupings(where={'close_date__ge': None}))
        assert len(groupings) + len(non_groupings) == len(all_groupings)
        assert set(groupings + non_groupings) == set(all_groupings)

        groupings = list(repository.iter_groupings(where={'close_date__gt': None}))
        non_groupings = list(repository.iter_groupings(where={
            'close_date__le': None, 'close_date__ne': None}))
        assert len(groupings) + len(non_groupings) == len(all_groupings)
        assert set(groupings + non_groupings) == set(all_groupings)

        no_groupings = list(repository.iter_groupings(
            where={'key__eq': uuid.uuid4()}))
        assert no_groupings == []


def test_iter_groupings_order(repository: Repository) -> None:
    """Order the list of groupings."""
    all_groupings = setup_groupings(repository, 7)  # Must be less than 10
    groupings = list(repository.iter_groupings(order=["name"]))
    assert groupings == all_groupings
    groupings = list(repository.iter_groupings(order=["+name"]))
    assert groupings == all_groupings
    groupings = list(repository.iter_groupings(order=["-name"]))
    assert groupings == list(reversed(all_groupings))


def test_set_registration(repository: Repository):
    """Test add / update of an registration."""
    registration = Registration(uuid.UUID(int=0), uuid.UUID(int=1), "data")
    assert registration == repository.set_registration(registration)


def test_get_registration(repository: Repository):
    """An inserted / updated registration can be retrieved."""
    registration = Registration(uuid.UUID(int=0), uuid.UUID(int=1), "data")
    repository.set_registration(registration)
    assert registration == repository.get_registration(
        registration.grouping, registration.participant)

    new_registration = registration._replace(data="atad")
    repository.set_registration(new_registration)
    assert repository.get_registration(
        registration.grouping, registration.participant).data == "atad"

    assert repository.get_registration(uuid.UUID(int=0), uuid.UUID(int=2)) is None


def test_iter_groupings_by_participant(repository):
    """List only applied groupings."""
    grouping = repository.set_grouping(create_grouping(repository))
    for uid in range(5):
        user_key = uuid.UUID(int=uid)
        repository.set_registration(Registration(grouping.key, user_key, ""))
        assert grouping == list(repository.iter_groupings_by_participant(user_key))[0]
