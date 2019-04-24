##
#    Copyright (c) 2019 Detlef Stern
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

"""Test the specifics of RAM-based repositories."""

from datetime import timedelta
from typing import Iterable, Optional, cast

from ....core.models import Grouping, GroupingKey, Permissions, User, UserKey
from ....core.utils import now
from ...base import (Connection, OrderSpec, UserGroup, UserRegistration,
                     WhereSpec)
from ..algebra import AlgebraConnection
from ..base import BaseProxyConnection


def test_ensure_iter_overwritten() -> None:
    """Make sure that all iter methods are overwritten by AlgebraConnection."""
    for name in dir(AlgebraConnection):
        if not name.startswith("iter_"):
            continue
        method = getattr(AlgebraConnection, name)
        assert method.__qualname__.startswith("AlgebraConnection.")


class MockConnection(BaseProxyConnection):
    """Connection that delivers values from iter methods."""

    def __init__(self, with_spec: bool):
        """Initialize the mock connection."""
        super().__init__(cast(Connection, None))
        self.with_spec = with_spec

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[User]:
        """Return an iterator of all or some users."""
        if self.with_spec:
            assert where is not None or order is not None
        return (
            User(UserKey(int=1), "host", Permissions.HOST),
            User(UserKey(int=3), "user"),
            User(UserKey(int=2), "tsoh", Permissions.HOST),
        )

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all or some groupings."""
        if self.with_spec:
            assert where is not None or order is not None
        host = User(UserKey(int=1), "host", Permissions.HOST)
        assert host.key is not None
        return (
            Grouping(
                GroupingKey(int=2), "code-2", "grp-2", host.key, now(), now(),
                now(), "P2", 6, 6, ""),
            Grouping(
                GroupingKey(int=3), "code-3", "grp-3", host.key, now(), now(),
                None, "P3", 3, 3, "3"),
            Grouping(
                GroupingKey(int=4), "code-4", "grp-4", host.key, now(), now(),
                None, "P4", 4, 4, "4"),
        )

    def iter_groupings_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        if self.with_spec:
            assert where is not None or order is not None
        return (
        )

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserRegistration]:
        """Return an iterator of user data of some user."""
        if self.with_spec:
            assert where is not None or order is not None
        return (
        )

    def iter_groups_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserGroup]:
        """Return an iterator of group data of some user."""
        if self.with_spec:
            assert where is not None or order is not None
        return (
        )


def get_connection(with_spec: bool = True) -> AlgebraConnection:
    """Create a new connection."""
    return AlgebraConnection(MockConnection(with_spec))


def test_iter_users_where() -> None:
    """Test the WhereSpec for iterating users."""
    assert len(list(get_connection(False).iter_users())) == 3
    connection = get_connection()
    users = list(connection.iter_users(where={'permissions__ne': Permissions.HOST}))
    assert len(users) == 1
    assert users[0].ident == "user"
    hosts = connection.iter_users(where={'permissions__eq': Permissions.HOST})
    assert len(list(hosts)) == 2
    users = list(connection.iter_users(where={'ident__eq': "tsoh"}))
    assert len(users) == 1
    assert users[0].ident == "tsoh"
    assert list(connection.iter_users(where={'ident__lt': "host"})) == []
    assert list(connection.iter_users(where={'ident__gt': "user"})) == []
    assert list(connection.iter_users(where={'ident__le': "host"}))[0].ident == "host"
    assert list(connection.iter_users(where={'ident__ge': "user"}))[0].ident == "user"


def test_iter_users_order() -> None:
    """Test the OrderSpec for iterating users."""
    connection = get_connection()
    users = connection.iter_users(order=['ident'])
    assert [user.ident for user in users] == ["host", "tsoh", "user"]
    users = connection.iter_users(order=['-ident'])
    assert [user.ident for user in users] == ["user", "tsoh", "host"]


def test_iter_users_where_order() -> None:
    """Test the WhereSpec together with OrderSpec for iterating users."""
    connection = get_connection()
    users = connection.iter_users(where={'ident__lt': "user"}, order=['+ident'])
    assert [user.ident for user in users] == ["host", "tsoh"]


def test_iter_groupings() -> None:
    """Check filtering/order of iterating groupings."""
    assert len(list(get_connection(False).iter_groupings())) == 3
    connection = get_connection()
    assert len(list(connection.iter_groupings(
        where={'host_key__eq': UserKey(int=1)}))) == 3
    assert not connection.iter_groupings(where={'host_key__eq': UserKey(int=2)})
    later = now() + timedelta(days=1)
    assert len(list(connection.iter_groupings(where={'close_date__le': later}))) == 3
    assert len(list(connection.iter_groupings(where={'close_date__lt': later}))) == 3
    assert len(list(connection.iter_groupings(where={'close_date__ge': later}))) == 2
    assert len(list(connection.iter_groupings(where={'close_date__gt': later}))) == 2


def test_iter_groupings_by_user() -> None:
    """Must delegate method call."""
    assert not get_connection(False).iter_groupings_by_user(UserKey(int=0))


def test_iter_user_registrations_by_grouping() -> None:
    """Must delegate method call."""
    assert not get_connection(False).iter_user_registrations_by_grouping(
        GroupingKey(int=0))


def test_iter_groups_by_user() -> None:
    """Must delegate method call."""
    assert not get_connection(False).iter_groups_by_user(UserKey(int=0))
