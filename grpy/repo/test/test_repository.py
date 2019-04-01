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

"""Test the repositories."""

import dataclasses  # pylint: disable=wrong-import-order
import datetime
import random
from typing import List, Tuple, cast

import pytest

from ... import utils
from ...models import (Grouping, GroupingKey, Groups, Permissions,
                       Registration, User, UserKey, UserPreferences)
from ...preferences import register_preferences
from .. import create_repository
from ..base import Connection, DuplicateKey
from ..ram import RamRepository

# pylint: disable=redefined-outer-name


def test_wrong_repository_url() -> None:
    """If an illegal URL ist given, a dummy repository must be returned."""
    repository = create_repository(cast(str, None))
    assert repository.url == "dummy:"
    assert create_repository("").url == "dummy:"


def test_no_connection(monkeypatch) -> None:
    """If unable to connect to data store, a dummy repository must be returned."""
    def return_false(_):
        return False
    monkeypatch.setattr(RamRepository, "can_connect", return_false)
    repository = create_repository("ram:")
    assert repository.url == "dummy:"


def test_no_initialize(monkeypatch) -> None:
    """If unable to initialize data store, a dummy repository must be returned."""
    def return_false(_):
        return False
    monkeypatch.setattr(RamRepository, "initialize", return_false)
    repository = create_repository("ram:")
    assert repository.url == "dummy:"


def test_has_errors(connection: Connection) -> None:
    """A new connection never has errors."""
    assert not connection.has_errors()


def test_insert_user(connection: Connection) -> None:
    """Check that inserting a new user works."""
    user = User(None, "user", Permissions.HOST)
    new_user = connection.set_user(user)
    assert not user.key
    assert new_user.key
    assert new_user.ident == user.ident
    assert new_user.is_host == user.is_host

    connection.set_user(user)
    assert "Duplicate key for field 'User.ident' with value 'user'" in \
        connection.get_messages()[0].text
    assert connection.get_messages() == []


def test_update_user(connection: Connection) -> None:
    """Check that updating an existing user works."""
    user = User(UserKey(), "user")
    connection.set_user(user)
    assert "Missing user: try to update key " in \
        connection.get_messages()[0].text
    assert connection.get_messages() == []

    user = connection.set_user(User(None, "user", Permissions.HOST))
    new_user = dataclasses.replace(user, permissions=Permissions(0))
    assert user.key == new_user.key
    newer_user = connection.set_user(new_user)
    assert new_user == newer_user

    user_2 = connection.set_user(User(None, "user_2"))
    renamed_user = dataclasses.replace(user_2, ident=user.ident)
    connection.set_user(renamed_user)
    assert "Duplicate key for field 'User.ident' with value 'user'" in \
        connection.get_messages()[0].text
    assert connection.get_messages() == []


def test_get_user(connection: Connection) -> None:
    """An inserted or updated user can be retrieved."""
    user = connection.set_user(User(None, "user", Permissions.HOST))
    assert user.key is not None
    new_user = connection.get_user(user.key)
    assert new_user == user

    newer_user = dataclasses.replace(user, permissions=Permissions(0))
    connection.set_user(newer_user)
    last_user = connection.get_user(user.key)
    assert last_user is not None
    assert last_user.is_host != user.is_host

    assert connection.get_user(UserKey()) is None


def test_get_user_by_ident(connection: Connection) -> None:
    """Retrieve an user by its ident."""
    user = connection.set_user(User(None, "user", Permissions.HOST))
    new_user = connection.get_user_by_ident(user.ident)
    assert new_user == user

    newer_user = dataclasses.replace(user, permissions=Permissions(0))
    connection.set_user(newer_user)
    last_user = connection.get_user_by_ident(user.ident)
    assert last_user is not None
    assert last_user.is_host != user.is_host

    for ident in ("", "invalid"):
        not_found = connection.get_user_by_ident(ident)
        assert not_found is None


def test_get_user_by_ident_change(connection: Connection) -> None:
    """After a change to an ident, the old name must not be accessible."""
    ident = "user"
    connection.set_user(User(None, ident))
    user = connection.get_user_by_ident(ident)
    assert user is not None
    user = dataclasses.replace(user, ident="resu")
    connection.set_user(user)
    assert connection.get_user_by_ident(ident) is None


def setup_users(connection: Connection, count: int) -> List[User]:
    """Insert some users into repository."""
    result = []
    permissions = Permissions(0)
    for i in range(count):
        user = connection.set_user(User(None, "user-%d" % i, permissions))
        result.append(user)
        permissions = Permissions(0) if permissions else Permissions.HOST
    return result


def test_iter_users(connection: Connection) -> None:
    """List all users."""
    all_users = setup_users(connection, 17)
    iter_users = utils.LazyList(connection.iter_users())
    assert len(iter_users) == len(all_users)
    assert set(iter_users) == set(all_users)


def test_iter_users_where(connection: Connection) -> None:
    """Select some user from list of all users."""
    all_users = setup_users(connection, 13)
    users = list(connection.iter_users(where={'permissions__eq': Permissions.HOST}))
    non_users = list(connection.iter_users(where={'permissions__ne': Permissions.HOST}))
    assert len(users) + len(non_users) == len(all_users)
    assert set(users + non_users) == set(all_users)

    for field in dataclasses.fields(User):
        field_name = field.name
        where = {field_name + "__eq": None}
        lazy_users = utils.LazyList(connection.iter_users(where=where))
        assert not lazy_users
        where = {field_name + "__ne": None}
        lazy_users = utils.LazyList(connection.iter_users(where=where))
        assert set(lazy_users) == set(all_users)

    for _ in range(len(all_users)):
        user = random.choice(all_users)
        users = list(connection.iter_users(where={'ident__eq': user.ident}))
        assert len(users) == 1
        assert users[0] == user

        other_users = list(connection.iter_users(where={'ident__ne': user.ident}))
        assert len(other_users) + 1 == len(all_users)
        assert set(other_users + users) == set(all_users)

        users = list(connection.iter_users(where={'ident__lt': user.ident}))
        non_users = list(connection.iter_users(where={'ident__ge': user.ident}))
        assert len(users) + len(non_users) == len(all_users)
        assert set(users + non_users) == set(all_users)

        users = list(connection.iter_users(where={'ident__gt': user.ident}))
        non_users = list(connection.iter_users(where={'ident__le': user.ident}))
        assert len(users) + len(non_users) == len(all_users)
        assert set(users + non_users) == set(all_users)

        no_users = utils.LazyList(connection.iter_users(
            where={'key__eq': UserKey()}))
        assert not no_users


def test_iter_users_order(connection: Connection) -> None:
    """Order the list of users."""
    all_users = setup_users(connection, 7)  # Must be less than 10
    users = list(connection.iter_users(order=["ident"]))
    assert users == all_users
    users = list(connection.iter_users(order=["+ident"]))
    assert users == all_users
    users = list(connection.iter_users(order=["-ident"]))
    assert users == list(reversed(all_users))


def test_insert_grouping(connection: Connection, grouping: Grouping) -> None:
    """Check that inserting a new grouping works."""
    new_grouping = connection.set_grouping(grouping)
    assert not grouping.key
    assert new_grouping.key
    assert new_grouping.code == grouping.code
    assert new_grouping.name == grouping.name
    assert new_grouping.host_key == grouping.host_key
    assert new_grouping.begin_date == grouping.begin_date
    assert new_grouping.final_date == grouping.final_date
    assert new_grouping.close_date == grouping.close_date
    assert new_grouping.policy == grouping.policy
    assert new_grouping.max_group_size == grouping.max_group_size
    assert new_grouping.member_reserve == grouping.member_reserve
    assert new_grouping.note == grouping.note

    with pytest.raises(DuplicateKey):
        connection.set_grouping(grouping)


def test_update_grouping(connection: Connection, grouping: Grouping) -> None:
    """Check that updating an existing grouping works."""
    grouping_1 = dataclasses.replace(grouping, key=GroupingKey())
    connection.set_grouping(grouping_1)
    assert "Missing grouping: try to update key " + str(grouping_1.key) in \
        connection.get_messages()[0].text
    assert connection.get_messages() == []

    grouping = connection.set_grouping(grouping)
    new_grouping = dataclasses.replace(grouping, name="new name")
    assert grouping.key == new_grouping.key
    newer_grouping = connection.set_grouping(new_grouping)
    assert new_grouping == newer_grouping


def test_update_grouping_duplicate(connection: Connection, grouping: Grouping) -> None:
    """Updating an existing grouping with duplicate code raises exception."""
    grouping = connection.set_grouping(grouping)
    grouping_2 = connection.set_grouping(
        dataclasses.replace(grouping, key=None, code=grouping.code[::-1]))
    with pytest.raises(DuplicateKey):
        connection.set_grouping(dataclasses.replace(grouping_2, code=grouping.code))


def test_get_grouping(connection: Connection, grouping: Grouping) -> None:
    """An inserted or updated grouping can be retrieved."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    new_grouping = connection.get_grouping(grouping.key)
    assert new_grouping == grouping

    newer_grouping = dataclasses.replace(grouping, name="new name")
    connection.set_grouping(newer_grouping)
    last_grouping = connection.get_grouping(grouping.key)
    assert last_grouping is not None
    assert last_grouping.name != grouping.name

    assert connection.get_grouping(GroupingKey()) is None


def test_get_grouping_by_code(connection: Connection, grouping: Grouping) -> None:
    """An inserted or updated grouping can be retrieved by short code."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    new_grouping = connection.get_grouping_by_code(grouping.code)
    assert new_grouping == grouping

    newer_grouping = dataclasses.replace(grouping, name="new name")
    connection.set_grouping(newer_grouping)
    last_grouping = connection.get_grouping(grouping.key)
    assert last_grouping is not None
    assert last_grouping.name != grouping.name

    for ident in ("", "invalid"):
        not_found = connection.get_user_by_ident(ident)
        assert not_found is None


def test_get_grouping_by_code_after_change(
        connection: Connection, grouping: Grouping) -> None:
    """After a change to a code, the old code must not be accessible."""
    grouping = connection.set_grouping(grouping)
    connection.set_grouping(dataclasses.replace(grouping, code="0000"))
    assert connection.get_grouping_by_code(grouping.code) is None


def setup_groupings(connection: Connection, count: int) -> List[Grouping]:
    """Insert some groupings into repository."""
    hosts = [
        connection.set_user(User(None, "host-1", Permissions.HOST)),
        connection.set_user(User(None, "host-2", Permissions.HOST)),
    ]
    for host in hosts:
        assert host.key is not None
    now = utils.now()
    timedelta = datetime.timedelta
    days = 0
    result = []
    for i in range(count):
        grouping = connection.set_grouping(Grouping(
            None, "cd%d" % i, "grouping-%d" % i,
            cast(UserKey, hosts[days % len(hosts)].key),
            now + timedelta(days=days), now + timedelta(days=days + 7), None,
            "RD", days + 1, 5, "Note %d" % i))
        result.append(grouping)
        days += 1
    return result


def test_iter_groupings(connection: Connection) -> None:
    """List all groupings."""
    all_groupings = setup_groupings(connection, 17)
    iter_groupings = utils.LazyList(connection.iter_groupings())
    assert len(iter_groupings) == len(all_groupings)
    assert set(iter_groupings) == set(all_groupings)


def test_iter_groupings_where(connection: Connection) -> None:
    """Select some grouping from list of all groupings."""
    all_groupings = setup_groupings(connection, 13)
    groupings = list(connection.iter_groupings(where={'close_date__eq': None}))
    non_groupings = list(connection.iter_groupings(where={'close_date__ne': None}))
    assert len(groupings) + len(non_groupings) == len(all_groupings)
    assert set(groupings + non_groupings) == set(all_groupings)

    groupings = list(connection.iter_groupings(where={'close_date__lt': utils.now()}))
    assert set(groupings) == set(all_groupings)
    groupings = list(connection.iter_groupings(where={'close_date__le': utils.now()}))
    assert set(groupings) == set(all_groupings)

    for _ in range(len(all_groupings)):
        grouping = random.choice(all_groupings)
        groupings = list(connection.iter_groupings(where={'name__eq': grouping.name}))
        assert len(groupings) == 1
        assert groupings[0] == grouping

        other_groupings = list(
            connection.iter_groupings(where={'name__ne': grouping.name}))
        assert len(other_groupings) + 1 == len(all_groupings)
        assert set(other_groupings + groupings) == set(all_groupings)

        groupings = list(connection.iter_groupings(where={
            'close_date__lt': None, 'close_date__ne': None}))
        non_groupings = list(connection.iter_groupings(where={'close_date__ge': None}))
        assert len(groupings) + len(non_groupings) == len(all_groupings)
        assert set(groupings + non_groupings) == set(all_groupings)

        groupings = list(connection.iter_groupings(where={'close_date__gt': None}))
        non_groupings = list(connection.iter_groupings(where={
            'close_date__le': None, 'close_date__ne': None}))
        assert len(groupings) + len(non_groupings) == len(all_groupings)
        assert set(groupings + non_groupings) == set(all_groupings)

        no_groupings = utils.LazyList(connection.iter_groupings(
            where={'key__eq': GroupingKey()}))
        assert not no_groupings


def test_iter_groupings_order(connection: Connection) -> None:
    """Order the list of groupings."""
    all_groupings = setup_groupings(connection, 7)  # Must be less than 10
    groupings = list(connection.iter_groupings(order=["name"]))
    assert groupings == all_groupings
    groupings = list(connection.iter_groupings(order=["+name"]))
    assert groupings == all_groupings
    groupings = list(connection.iter_groupings(order=["-name"]))
    assert groupings == list(reversed(all_groupings))


def test_set_registration(connection: Connection, grouping: Grouping) -> None:
    """Test add / update of an registration."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    user = connection.set_user(User(None, "UsER"))
    assert user.key is not None

    registration = Registration(grouping.key, user.key, UserPreferences())
    assert registration == connection.set_registration(registration)


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class Prefs(UserPreferences):
    """Test-Class to have some other preferences."""

    position: int


register_preferences('tstP', Prefs)


def test_get_registration(connection: Connection, grouping: Grouping) -> None:
    """An inserted / updated registration can be retrieved."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    user = connection.set_user(User(None, "UsER"))
    assert user.key is not None

    registration = Registration(grouping.key, user.key, UserPreferences())
    connection.set_registration(registration)
    assert registration == connection.get_registration(
        registration.grouping_key, registration.user_key)

    prefs = Prefs(1)
    new_registration = dataclasses.replace(registration, preferences=prefs)
    connection.set_registration(new_registration)
    newer_registration = connection.get_registration(
        registration.grouping_key, registration.user_key)
    assert newer_registration is not None
    assert newer_registration.preferences == prefs

    assert connection.get_registration(grouping.key, UserKey(int=2)) is None


def test_count_registrations_by_grouping(
        connection: Connection, grouping: Grouping) -> None:
    """Test the count calculation for a grouping."""

    # An non-existing grouping has no registrations
    assert connection.count_registrations_by_grouping(GroupingKey()) == 0

    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    assert connection.count_registrations_by_grouping(grouping.key) == 0

    for i in range(10):
        user = connection.set_user(User(None, "USeR" + str(i)))
        assert user.key is not None
        connection.set_registration(Registration(
            grouping.key, user.key, UserPreferences()))
        assert connection.count_registrations_by_grouping(grouping.key) == i + 1


def test_delete_registration(connection: Connection, grouping: Grouping) -> None:
    """A deleted registration cannot be retrieved."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    user = connection.set_user(User(None, "UseR"))
    assert user.key is not None

    registration = Registration(grouping.key, user.key, UserPreferences())
    connection.set_registration(registration)

    connection.delete_registration(grouping.key, user.key)
    assert connection.get_registration(grouping.key, user.key) is None
    connection.delete_registration(grouping.key, user.key)
    assert connection.get_registration(grouping.key, user.key) is None


def test_iter_groupings_by_user(connection: Connection, grouping: Grouping) -> None:
    """List only applied groupings."""
    other_grouping = dataclasses.replace(grouping, code="newcode", name="Another name")
    assert grouping != other_grouping
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    other_grouping = connection.set_grouping(other_grouping)
    assert other_grouping.key != grouping.key
    for uid in range(5):
        user = connection.set_user(User(None, "USER" + str(uid)))
        assert user.key is not None
        connection.set_registration(Registration(
            grouping.key, user.key, UserPreferences()))
        assert [grouping] == list(connection.iter_groupings_by_user(user.key))
        assert list(connection.iter_groupings_by_user(
            user.key, where={'name__ne': grouping.name})) == []


def test_iter_user_registrations_by_grouping(
        connection: Connection, grouping: Grouping) -> None:
    """Iterate over all user data of registrations."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    for i in range(7):
        user = connection.set_user(User(None, "user-%d" % i))
        assert user.key is not None
        connection.set_registration(Registration(
            grouping.key, user.key, UserPreferences()))
        assert len(utils.LazyList(connection.iter_user_registrations_by_grouping(
            grouping.key))) == i + 1
    assert not utils.LazyList(connection.iter_user_registrations_by_grouping(
        GroupingKey(int=111)))


def insert_groups(
        connection: Connection, grouping: Grouping) -> Tuple[List[User], Groups]:
    """Create a tuple of result groups for a grouping."""
    users = [connection.set_user(User(None, "user=%03d" % i)) for i in range(20)]
    user_list = list(users)
    group_list = []
    while user_list:
        group_size = random.randint(3, 7)
        group = frozenset(cast(UserKey, user.key) for user in user_list[-group_size:])
        group_list.append(group)
        user_list = user_list[:-group_size]
    groups = tuple(group_list)

    assert grouping.key is not None
    connection.set_groups(grouping.key, groups)
    assert users
    assert groups
    return (users, groups)


def test_set_get_groups(connection: Connection, grouping: Grouping) -> None:
    """Setting / replacing a group works."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    assert connection.get_groups(grouping.key) == ()
    _, groups = insert_groups(connection, grouping)
    assert connection.get_groups(grouping.key) == groups

    smaller_groups = groups[1:]
    connection.set_groups(grouping.key, smaller_groups)
    assert connection.get_groups(grouping.key) == smaller_groups
    connection.set_groups(grouping.key, groups)
    assert connection.get_groups(grouping.key) == groups


def test_iter_groups_by_user(connection: Connection, grouping: Grouping) -> None:
    """Is a user belongs to some groups, return that groups."""
    grouping = connection.set_grouping(grouping)
    users, groups = insert_groups(connection, grouping)
    for user in users:
        assert user.key is not None
        named_user_groups = list(connection.iter_groups_by_user(user.key))
        assert named_user_groups
        for named_user_group in named_user_groups:
            assert named_user_group.grouping_key == grouping.key
            assert named_user_group.grouping_name == grouping.name
            assert frozenset(user.user_key for user in named_user_group.group) in groups
