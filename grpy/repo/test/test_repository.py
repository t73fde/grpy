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
from typing import List, Tuple, cast

import pytest

from .. import create_factory
from ..base import DuplicateKey, NothingToUpdate, Repository
from ..ram import RamRepositoryFactory
from ... import utils
from ...models import (
    Grouping, Groups, Permission, Registration, User, UserPreferences)

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
    assert new_user.ident == user.ident
    assert new_user.is_host == user.is_host

    with pytest.raises(DuplicateKey):
        repository.set_user(user)


def test_update_user(repository: Repository):
    """Check that updating an existing user works."""
    user = User(uuid.uuid4(), "user")
    with pytest.raises(NothingToUpdate):
        repository.set_user(user)

    user = repository.set_user(User(None, "user", Permission.HOST))
    new_user = user._replace(permission=Permission(0))
    assert user.key == new_user.key
    newer_user = repository.set_user(new_user)
    assert new_user == newer_user

    user_2 = repository.set_user(User(None, "user_2"))
    renamed_user = user_2._replace(ident=user.ident)
    with pytest.raises(DuplicateKey):
        repository.set_user(renamed_user)


def test_get_user(repository: Repository):
    """An inserted or updated user can be retrieved."""
    user = repository.set_user(User(None, "user", Permission.HOST))
    assert user.key is not None
    new_user = repository.get_user(user.key)
    assert new_user == user

    newer_user = user._replace(permission=Permission(0))
    repository.set_user(newer_user)
    last_user = repository.get_user(user.key)
    assert last_user is not None
    assert last_user.is_host != user.is_host

    assert repository.get_user(uuid.uuid4()) is None


def test_get_user_by_ident(repository: Repository):
    """Retrieve an user by its ident."""
    user = repository.set_user(User(None, "user", Permission.HOST))
    new_user = repository.get_user_by_ident(user.ident)
    assert new_user == user

    newer_user = user._replace(permission=Permission(0))
    repository.set_user(newer_user)
    last_user = repository.get_user_by_ident(user.ident)
    assert last_user is not None
    assert last_user.is_host != user.is_host

    for ident in ("", "invalid"):
        not_found = repository.get_user_by_ident(ident)
        assert not_found is None


def test_get_user_by_ident_change(repository: Repository):
    """After a change to an ident, the old name must not be accessible."""
    ident = "user"
    repository.set_user(User(None, ident))
    user = repository.get_user_by_ident(ident)
    assert user is not None
    user = user._replace(ident="resu")
    repository.set_user(user)
    assert repository.get_user_by_ident(ident) is None


def setup_users(repository: Repository, count: int) -> List[User]:
    """Insert some users into repository."""
    result = []
    permission = Permission(0)
    for i in range(count):
        user = repository.set_user(User(None, "user-%d" % i, permission))
        result.append(user)
        permission = Permission(0) if permission else Permission.HOST
    return result


def test_iter_users(repository: Repository) -> None:
    """List all users."""
    all_users = setup_users(repository, 17)
    iter_users = utils.LazyList(repository.iter_users())
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
        lazy_users = utils.LazyList(repository.iter_users(where=where))
        assert not lazy_users
        where = {field_name + "__ne": None}
        lazy_users = utils.LazyList(repository.iter_users(where=where))
        assert set(lazy_users) == set(all_users)

    for _ in range(len(all_users)):
        user = random.choice(all_users)
        users = list(repository.iter_users(where={'ident__eq': user.ident}))
        assert len(users) == 1
        assert users[0] == user

        other_users = list(repository.iter_users(where={'ident__ne': user.ident}))
        assert len(other_users) + 1 == len(all_users)
        assert set(other_users + users) == set(all_users)

        users = list(repository.iter_users(where={'ident__lt': user.ident}))
        non_users = list(repository.iter_users(where={'ident__ge': user.ident}))
        assert len(users) + len(non_users) == len(all_users)
        assert set(users + non_users) == set(all_users)

        users = list(repository.iter_users(where={'ident__gt': user.ident}))
        non_users = list(repository.iter_users(where={'ident__le': user.ident}))
        assert len(users) + len(non_users) == len(all_users)
        assert set(users + non_users) == set(all_users)

        no_users = utils.LazyList(repository.iter_users(
            where={'key__eq': uuid.uuid4()}))
        assert not no_users


def test_iter_users_order(repository: Repository) -> None:
    """Order the list of users."""
    all_users = setup_users(repository, 7)  # Must be less than 10
    users = list(repository.iter_users(order=["ident"]))
    assert users == all_users
    users = list(repository.iter_users(order=["+ident"]))
    assert users == all_users
    users = list(repository.iter_users(order=["-ident"]))
    assert users == list(reversed(all_users))


def test_insert_grouping(repository: Repository, grouping: Grouping):
    """Check that inserting a new grouping works."""
    new_grouping = repository.set_grouping(grouping)
    assert not grouping.key
    assert new_grouping.key
    assert new_grouping.code == grouping.code
    assert new_grouping.name == grouping.name
    assert new_grouping.host == grouping.host
    assert new_grouping.begin_date == grouping.begin_date
    assert new_grouping.final_date == grouping.final_date
    assert new_grouping.close_date == grouping.close_date
    assert new_grouping.policy == grouping.policy
    assert new_grouping.max_group_size == grouping.max_group_size
    assert new_grouping.member_reserve == grouping.member_reserve
    assert new_grouping.note == grouping.note

    with pytest.raises(DuplicateKey):
        repository.set_grouping(grouping)


def test_update_grouping(repository: Repository, grouping: Grouping):
    """Check that updating an existing grouping works."""
    grouping_1 = grouping._replace(key=uuid.uuid4())
    with pytest.raises(NothingToUpdate):
        repository.set_grouping(grouping_1)

    grouping = repository.set_grouping(grouping)
    new_grouping = grouping._replace(name="new name")
    assert grouping.key == new_grouping.key
    newer_grouping = repository.set_grouping(new_grouping)
    assert new_grouping == newer_grouping


def test_get_grouping(repository: Repository, grouping: Grouping):
    """An inserted or updated grouping can be retrieved."""
    grouping = repository.set_grouping(grouping)
    assert grouping.key is not None
    new_grouping = repository.get_grouping(grouping.key)
    assert new_grouping == grouping

    newer_grouping = grouping._replace(name="new name")
    repository.set_grouping(newer_grouping)
    last_grouping = repository.get_grouping(grouping.key)
    assert last_grouping.name != grouping.name

    assert repository.get_grouping(uuid.uuid4()) is None


def test_get_grouping_by_code(repository: Repository, grouping: Grouping):
    """An inserted or updated grouping can be retrieved by short code."""
    grouping = repository.set_grouping(grouping)
    assert grouping.key is not None
    new_grouping = repository.get_grouping_by_code(grouping.code)
    assert new_grouping == grouping

    newer_grouping = grouping._replace(name="new name")
    repository.set_grouping(newer_grouping)
    last_grouping = repository.get_grouping(grouping.key)
    assert last_grouping.name != grouping.name

    for ident in ("", "invalid"):
        not_found = repository.get_user_by_ident(ident)
        assert not_found is None


def test_get_grouping_by_code_after_change(repository: Repository, grouping: Grouping):
    """After a change to a code, the old code must not be accessible."""
    grouping = repository.set_grouping(grouping)
    repository.set_grouping(grouping._replace(code="0000"))
    assert repository.get_grouping_by_code(grouping.code) is None


def setup_groupings(repository: Repository, count: int) -> List[Grouping]:
    """Insert some groupings into repository."""
    hosts = [
        repository.set_user(User(None, "host-1", Permission.HOST)),
        repository.set_user(User(None, "host-2", Permission.HOST)),
    ]
    for host in hosts:
        assert host.key is not None
    now = utils.now()
    timedelta = datetime.timedelta
    days = 0
    result = []
    for i in range(count):
        grouping = repository.set_grouping(Grouping(
            None, "cd%d" % i, "grouping-%d" % i,
            cast(uuid.UUID, hosts[days % len(hosts)].key),
            now + timedelta(days=days), now + timedelta(days=days + 7), None,
            "RD", days + 1, 5, "Note %d" % i))
        result.append(grouping)
        days += 1
    return result


def test_iter_groupings(repository: Repository) -> None:
    """List all groupings."""
    all_groupings = setup_groupings(repository, 17)
    iter_groupings = utils.LazyList(repository.iter_groupings())
    assert len(iter_groupings) == len(all_groupings)
    assert set(iter_groupings) == set(all_groupings)


def test_iter_groupings_where(repository: Repository) -> None:
    """Select some grouping from list of all groupings."""
    all_groupings = setup_groupings(repository, 13)
    groupings = list(repository.iter_groupings(where={'close_date__eq': None}))
    non_groupings = list(repository.iter_groupings(where={'close_date__ne': None}))
    assert len(groupings) + len(non_groupings) == len(all_groupings)
    assert set(groupings + non_groupings) == set(all_groupings)

    groupings = list(repository.iter_groupings(where={'close_date__lt': utils.now()}))
    assert set(groupings) == set(all_groupings)
    groupings = list(repository.iter_groupings(where={'close_date__le': utils.now()}))
    assert set(groupings) == set(all_groupings)

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

        no_groupings = utils.LazyList(repository.iter_groupings(
            where={'key__eq': uuid.uuid4()}))
        assert not no_groupings


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
    registration = Registration(uuid.UUID(int=0), uuid.UUID(int=1), UserPreferences())
    assert registration == repository.set_registration(registration)


def test_get_registration(repository: Repository):
    """An inserted / updated registration can be retrieved."""
    registration = Registration(uuid.UUID(int=0), uuid.UUID(int=1), UserPreferences())
    repository.set_registration(registration)
    assert registration == repository.get_registration(
        registration.grouping, registration.participant)

    class Prefs(UserPreferences):
        """Test-Class to have some other preferences."""

        def __new__(cls, position: int):
            """Create new tuple."""
            self = super().__new__(cls)
            self.position = position
            return self

    prefs = Prefs(1)
    new_registration = registration._replace(preferences=prefs)
    repository.set_registration(new_registration)
    assert repository.get_registration(
        registration.grouping, registration.participant).preferences == prefs

    assert repository.get_registration(uuid.UUID(int=0), uuid.UUID(int=2)) is None


def test_count_registrations_by_grouping(repository: Repository, grouping: Grouping):
    """Test the count calculation for a grouping."""

    # An non-existing grouping has no registrations
    assert repository.count_registrations_by_grouping(uuid.uuid4()) == 0

    grouping = repository.set_grouping(grouping)
    assert grouping.key is not None
    assert repository.count_registrations_by_grouping(grouping.key) == 0

    for i in range(10):
        repository.set_registration(Registration(
            grouping.key, uuid.UUID(int=i), UserPreferences()))
        assert repository.count_registrations_by_grouping(grouping.key) == i + 1


def test_delete_registration(repository: Repository):
    """A deleted registration cannot be retrieved."""
    registration = Registration(uuid.UUID(int=0), uuid.UUID(int=1), UserPreferences())
    repository.set_registration(registration)

    repository.delete_registration(uuid.UUID(int=0), uuid.UUID(int=1))
    assert repository.get_registration(uuid.UUID(int=0), uuid.UUID(int=1)) is None
    repository.delete_registration(uuid.UUID(int=0), uuid.UUID(int=1))
    assert repository.get_registration(uuid.UUID(int=0), uuid.UUID(int=1)) is None


def test_iter_groupings_by_participant(repository: Repository, grouping: Grouping):
    """List only applied groupings."""
    grouping = repository.set_grouping(grouping)
    assert grouping.key is not None
    for uid in range(5):
        user_key = uuid.UUID(int=uid)
        repository.set_registration(Registration(
            grouping.key, user_key, UserPreferences()))
        assert grouping == list(repository.iter_groupings_by_participant(user_key))[0]


def test_iter_user_registrations_by_grouping(repository: Repository):
    """Iterate over all user data of registrations."""
    for i in range(7):
        user = repository.set_user(User(None, "user-%d" % i))
        assert user.key is not None
        repository.set_registration(Registration(
            uuid.UUID(int=100), user.key, UserPreferences()))
        assert len(utils.LazyList(repository.iter_user_registrations_by_grouping(
            uuid.UUID(int=100)))) == i + 1
    assert not utils.LazyList(repository.iter_user_registrations_by_grouping(
        uuid.UUID(int=111)))


def insert_groups(
        repository: Repository, grouping: Grouping) -> Tuple[List[User], Groups]:
    """Create a tuple of result groups for a grouping."""
    users = [repository.set_user(User(None, "user=%03d" % i)) for i in range(20)]
    user_list = list(users)
    group_list = []
    while user_list:
        group_size = random.randint(3, 7)
        group = frozenset(user.key for user in user_list[-group_size:])
        group_list.append(group)
        user_list = user_list[:-group_size]
    groups = tuple(group_list)

    assert grouping.key is not None
    repository.set_groups(grouping.key, groups)
    assert users
    assert groups
    return (users, groups)


def test_set_get_groups(repository: Repository, grouping: Grouping):
    """Setting / replacing a group works."""
    grouping = repository.set_grouping(grouping)
    assert repository.get_groups(grouping.key) == ()
    _, groups = insert_groups(repository, grouping)
    assert repository.get_groups(grouping.key) == groups


def test_iter_groups_by_user(repository: Repository, grouping: Grouping):
    """Is a user belongs to some groups, return that groups."""
    grouping = repository.set_grouping(grouping)
    users, groups = insert_groups(repository, grouping)
    for user in users:
        assert user.key is not None
        user_groups = list(repository.iter_groups_by_user(user.key))
        assert user_groups
        for user_group in user_groups:
            assert user_group.grouping == grouping.key
            assert user_group.name == grouping.name
            assert user_group.group in groups
