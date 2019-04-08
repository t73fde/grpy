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

"""SQLite-based repository."""

import dataclasses  # pylint: disable=wrong-import-order
import sqlite3
from datetime import datetime
from typing import (AbstractSet, Any, Iterable, List, Optional, Sequence,
                    Tuple, cast)
from urllib.parse import urlparse

from pytz import utc

from ..models import (Grouping, GroupingKey, GroupingState, Groups,
                      Permissions, Registration, User, UserKey)
from .base import (Connection, DuplicateKey, Message, NothingToUpdate,
                   OrderSpec, Repository, WhereSpec)
from .logic import decode_preferences, encode_preferences
from .models import NamedUser, UserGroup, UserRegistration

sqlite3.register_adapter(UserKey, lambda u: u.bytes_le)
sqlite3.register_converter('USER_KEY', lambda b: UserKey(bytes_le=b))
sqlite3.register_adapter(GroupingKey, lambda u: u.bytes_le)
sqlite3.register_converter('GROUPING_KEY', lambda b: GroupingKey(bytes_le=b))
sqlite3.register_adapter(
    datetime, lambda d: d.strftime("%Y%m%d-%H%M%S.%f"))
sqlite3.register_converter(
    'DATETIME',
    lambda b: datetime.strptime(
        b.decode('utf-8'), "%Y%m%d-%H%M%S.%f").replace(tzinfo=utc))


class SqliteRepository(Repository):
    """Maintain SQLite-based repository."""

    def __init__(self, repository_url: str):
        """Initialize the repository."""
        parsed_url = urlparse(repository_url)
        if parsed_url.scheme != "sqlite":
            raise ValueError(
                "SqliteRepository cannot handle scheme: {}".format(
                    parsed_url.scheme))
        parsed_url = parsed_url._replace(
            netloc="", params='', query='', fragment='')
        super().__init__(parsed_url.geturl())

        if parsed_url.path:
            self._database: Optional[str] = parsed_url.path
            self._connection_class = SqliteConnection
        else:
            self._database = None
            self._connection_class = SqliteMemoryConnection
        self._connection: Optional[sqlite3.Connection] = None

    def _connect(self) -> Optional[sqlite3.Connection]:
        """Connect to the database or return None."""
        if self._database:
            try:
                connection = sqlite3.connect(
                    self._database, detect_types=sqlite3.PARSE_DECLTYPES)
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("BEGIN TRANSACTION")
                return connection
            except Exception:  # pylint: disable=broad-except
                return None

        if not self._connection:
            self._connection = sqlite3.connect(
                ":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def can_connect(self) -> bool:
        """Test the connection to the data source."""
        connection = self._connect()
        if connection:
            connection.execute("SELECT name FROM sqlite_master")
            if self._database:
                connection.close()
            return True
        return False

    def initialize(self) -> bool:
        """Initialize the repository, if needed."""
        connection = self._connect()
        if not connection:
            return False
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            tables = {row[0] for row in cursor.fetchall()}
            if "users" not in tables:
                cursor.execute("""
CREATE TABLE users(
    key USER_KEY PRIMARY KEY,
    ident TEXT UNIQUE NOT NULL,
    permissions INT)
""")
            if "groupings" not in tables:
                cursor.execute("""
CREATE TABLE groupings(
    key GROUPING_KEY PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    host_key USER_KEY NOT NULL,
    begin_date DATETIME NOT NULL,
    final_date DATETIME NOT NULL,
    close_date DATETIME,
    policy TEXT NOT NULL,
    max_group_size INT NOT NULL,
    member_reserve INT NOT NULL,
    note TEXT NOT NULL,
    FOREIGN KEY(host_key) REFERENCES users(key))
""")
            if "registrations" not in tables:
                cursor.execute("""
CREATE TABLE registrations(
    grouping_key GROUPING_KEY NOT NULL,
    user_key USER_KEY NOT NULL,
    preferences TEXT NOT NULL,
    PRIMARY KEY(grouping_key, user_key),
    FOREIGN KEY(grouping_key) REFERENCES groupings(key),
    FOREIGN KEY(user_key) REFERENCES users(key))
""")
            if "groups" not in tables:
                cursor.execute("""
CREATE TABLE groups(
    grouping_key GROUPING_KEY NOT NULL,
    group_no INT NOT NULL,
    user_key USER_KEY NOT NULL,
    FOREIGN KEY(grouping_key) REFERENCES groupings(key),
    FOREIGN KEY(user_key) REFERENCES users(key))
""")
                cursor.execute("""
CREATE INDEX idx_groups ON groups(grouping_key)
""")
            if self._database:
                cursor.execute("COMMIT")
        finally:
            cursor.close()
        return True

    def create(self) -> Connection:
        """Create and setup a connection."""
        return self._connection_class(self._connect())


class SqliteConnection(Connection):  # pylint: disable=too-many-public-methods
    """SQLite-based connection."""

    def __init__(self, connection):
        """Initialize the connection."""
        self._connection = connection
        self._messages: List[Message] = []
        self._has_errors: bool = False

    def _add_message(self, category: str, text: str) -> None:
        """Add a new message."""
        self._messages.append(Message(category, text))
        self._has_errors = True

    def get_messages(self) -> Sequence[Message]:
        """Return all connection-related messages."""
        result = self._messages
        self._messages = []
        return result

    def has_errors(self) -> bool:
        """Return True if some errors were detected with this connection."""
        return self._has_errors

    def close(self, success: bool):
        """Close the connection."""
        if success:
            self._execute("COMMIT")
        self._connection.close()
        self._connection = None

    def _execute(
            self, sql: str, values: Sequence[Any] = ()) -> sqlite3.Cursor:
        """Execute a SQL command."""
        return cast(sqlite3.Cursor, self._connection.execute(sql, values))

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        if user.key:
            cursor = self._execute(
                "SELECT ident FROM users WHERE key=?", (user.key,))
            row = cursor.fetchone()
            cursor.close()
            if not row:
                raise NothingToUpdate("Missing user", user.key)
            try:
                self._execute(
                    "UPDATE users SET ident=?, permissions=? WHERE key=?",
                    (user.ident, user.permissions.value, user.key))
            except sqlite3.IntegrityError as exc:
                if exc.args[0] == 'UNIQUE constraint failed: users.ident':
                    raise DuplicateKey("User.ident", user.ident)
                raise
            return user

        user_key = UserKey()
        try:
            self._execute(
                "INSERT INTO users VALUES(?,?,?)",
                (user_key, user.ident, user.permissions.value))
        except sqlite3.IntegrityError as exc:
            if exc.args[0] == 'UNIQUE constraint failed: users.ident':
                raise DuplicateKey("User.ident", user.ident)
            raise
        return dataclasses.replace(user, key=user_key)

    def get_user(self, user_key: UserKey) -> Optional[User]:
        """Return user with given key or None."""
        cursor = self._execute(
            "SELECT ident, permissions FROM users WHERE key=?", (user_key,))
        row = cursor.fetchone()
        cursor.close()
        return User(user_key, row[0], Permissions(row[1])) if row else None

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user with given ident, or None."""
        cursor = self._execute(
            "SELECT key, permissions FROM users WHERE ident=?", (ident,))
        row = cursor.fetchone()
        cursor.close()
        return User(row[0], ident, Permissions(row[1])) if row else None

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[User]:
        """Return an iterator of all or some users."""
        where_sql, where_vals = where_clause(where)
        cursor = self._execute(
            "SELECT key, ident, permissions FROM users" +  # nosec
            where_sql + order_clause(order), where_vals)
        result = [
            User(row[0], row[1], Permissions(row[2])) for row in cursor.fetchall()]
        cursor.close()
        return result

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        if grouping.key:
            cursor = self._execute(
                "SELECT code FROM groupings WHERE key=?", (grouping.key,))
            row = cursor.fetchone()
            cursor.close()
            if not row:
                raise NothingToUpdate("Missing grouping", grouping.key)
            try:
                self._execute(
                    "UPDATE groupings SET code=?, name=?, host_key=?, "
                    "begin_date=?,final_date=?,close_date=?,policy=?, "
                    "max_group_size=?,member_reserve=?,note=? WHERE key=?",
                    (grouping.code, grouping.name, grouping.host_key,
                        grouping.begin_date, grouping.final_date,
                        grouping.close_date, grouping.policy,
                        grouping.max_group_size, grouping.member_reserve,
                        grouping.note, grouping.key))
            except sqlite3.IntegrityError as exc:
                if exc.args[0] == 'UNIQUE constraint failed: groupings.code':
                    raise DuplicateKey("Grouping.code", grouping.code)
                raise
            return grouping

        grouping_key = GroupingKey()
        try:
            self._execute(
                "INSERT INTO groupings VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (grouping_key, grouping.code, grouping.name, grouping.host_key,
                    grouping.begin_date, grouping.final_date, grouping.close_date,
                    grouping.policy, grouping.max_group_size,
                    grouping.member_reserve, grouping.note))
        except sqlite3.IntegrityError as exc:
            if exc.args[0] == 'UNIQUE constraint failed: groupings.code':
                raise DuplicateKey("Grouping.code", grouping.code)
            raise
        return dataclasses.replace(grouping, key=grouping_key)

    def get_grouping(self, grouping_key: GroupingKey) -> Optional[Grouping]:
        """Return grouping with given key."""
        cursor = self._execute(
            "SELECT code, name, host_key, begin_date, final_date, close_date, "
            "policy, max_group_size, member_reserve, note FROM groupings WHERE key=?",
            (grouping_key,))
        row = cursor.fetchone()
        cursor.close()
        return Grouping(
            grouping_key, row[0], row[1], row[2], row[3], row[4], row[5],
            row[6], row[7], row[8], row[9]) if row else None

    def get_grouping_by_code(self, code: str) -> Optional[Grouping]:
        """Return grouping with given short code."""
        cursor = self._execute(
            "SELECT key, name, host_key, begin_date, final_date, close_date, "
            "policy, max_group_size, member_reserve, note FROM groupings WHERE code=?",
            (code,))
        row = cursor.fetchone()
        cursor.close()
        return Grouping(
            row[0], code, row[1], row[2], row[3], row[4], row[5],
            row[6], row[7], row[8], row[9]) if row else None

    def get_grouping_state(self, grouping_key: GroupingKey) -> GroupingState:
        """Return current state of given grouping."""
        cursor = self._execute(
            "SELECT begin_date, final_date, close_date FROM groupings WHERE key=?",
            (grouping_key,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return GroupingState.UNKNOWN
        state = Grouping(
            None, " code ", " name ", UserKey(int=0), row[0], row[1], row[2],
            "RD", 7, 7, "").get_state()
        if state not in (GroupingState.FINAL, GroupingState.CLOSED):
            return state
        has_regs = bool(self.count_registrations_by_grouping(grouping_key))
        cursor = self._execute(
            "SELECT COUNT(*) FROM groups WHERE grouping_key=?", (grouping_key,))
        row = cursor.fetchone()
        cursor.close()
        has_groups = bool(row[0])
        if has_groups:
            if has_regs:
                return GroupingState.GROUPED
            if state == GroupingState.FINAL:
                return GroupingState.FASTENED
            return GroupingState.CLOSED
        return GroupingState.FINAL

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all or some groupings."""
        where_sql, where_vals = where_clause(where, {"close_date"})
        cursor = self._execute(
            "SELECT key, code, name, host_key, begin_date, final_date, "  # nosec
            "close_date, policy, max_group_size, member_reserve, note "
            "FROM groupings" + where_sql + order_clause(order), where_vals)
        result = []
        for row in cursor.fetchall():
            result.append(Grouping(*row))
        cursor.close()
        return result

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        encoded = encode_preferences(registration.preferences)
        if encoded is None:
            self._add_message(
                'critical',
                "Unable to store preferences of type {}. "
                "Please consult your administrator.".format(
                    type(registration.preferences)))
            return registration
        cursor = self._execute(
            "SELECT preferences FROM registrations WHERE grouping_key=? AND user_key=?",
            (registration.grouping_key, registration.user_key))
        row = cursor.fetchone()
        cursor.close()
        if row:
            self._execute(
                "UPDATE registrations SET preferences=?"
                "WHERE grouping_key=? AND user_key=?",
                (encoded, registration.grouping_key, registration.user_key))
            return registration
        self._execute(
            "INSERT INTO registrations VALUES(?,?,?)",
            (registration.grouping_key, registration.user_key, encoded))
        return registration

    def get_registration(
            self,
            grouping_key: GroupingKey, user_key: UserKey) -> Optional[Registration]:
        """Return registration with given grouping and user."""
        cursor = self._execute(
            "SELECT preferences FROM registrations WHERE grouping_key=? AND user_key=?",
            (grouping_key, user_key))
        row = cursor.fetchone()
        cursor.close()
        if row:
            preferences = decode_preferences(row[0])
            if preferences:
                return Registration(grouping_key, user_key, preferences)
        return None

    def count_registrations_by_grouping(self, grouping_key: GroupingKey) -> int:
        """Return number of registration for given grouping."""
        cursor = self._execute(
            "SELECT COUNT(user_key) FROM registrations WHERE grouping_key=?",
            (grouping_key,))
        row = cursor.fetchone()
        cursor.close()
        return cast(int, row[0])

    def delete_registration(self, grouping_key: GroupingKey, user_key: UserKey) -> None:
        """Delete the given registration from the repository."""
        self._execute(
            "DELETE FROM registrations WHERE grouping_key=? AND user_key=?",
            (grouping_key, user_key))

    def delete_registrations(self, grouping_key: GroupingKey) -> None:
        """Delete all registrations of a grouping from the repository."""
        self._execute(
            "DELETE FROM registrations WHERE grouping_key=?", (grouping_key, ))

    def iter_groupings_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        where_sql, where_vals = where_clause(where, {"close_date"}, no_where=True)
        cursor = self._execute(
            "SELECT key, code, name, host_key, begin_date, final_date, "  # nosec
            "close_date, policy, max_group_size, member_reserve, note "
            "FROM groupings, registrations WHERE "
            "key=grouping_key AND user_key=?" + where_sql + order_clause(order),
            [user_key] + where_vals)
        result = []
        for row in cursor.fetchall():
            result.append(Grouping(*row))
        cursor.close()
        return result

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserRegistration]:
        """Return an iterator of user data of some user."""
        where_sql, where_vals = where_clause(where, no_where=True)
        cursor = self._execute(
            "SELECT key, ident, permissions, preferences "  # nosec
            "FROM users, registrations "
            "WHERE key=user_key AND grouping_key=?" + where_sql + order_clause(order),
            [grouping_key] + where_vals)
        result = []
        for row in cursor.fetchall():
            preferences = decode_preferences(row[3])
            if preferences:
                result.append(UserRegistration(
                    User(row[0], row[1], Permissions(row[2])), preferences))
        cursor.close()
        return result

    def set_groups(self, grouping_key: GroupingKey, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        cursor = self._execute(
            "SELECT group_no, user_key FROM groups WHERE grouping_key=?",
            (grouping_key,))
        in_db = {(grouping_key, row[0], row[1]) for row in cursor.fetchall()}
        cursor.close()
        to_db = set()
        for group_no, group in enumerate(groups):
            for user_key in group:
                to_db.add((grouping_key, group_no, user_key))
        for group_data in to_db - in_db:
            self._execute(
                "INSERT INTO groups VALUES(?,?,?)", group_data)
        for group_data in in_db - to_db:
            self._execute(
                "DELETE FROM groups WHERE "
                "grouping_key=? AND group_no=? AND user_key=?", group_data)

    def get_groups(self, grouping_key: GroupingKey) -> Groups:
        """Get groups builded for grouping."""
        cursor = self._execute(
            "SELECT group_no, user_key FROM groups "
            "WHERE grouping_key=? ORDER BY group_no", (grouping_key,))
        result = []
        current_group_no = -1
        current_group: List[UserKey] = []
        for row in cursor.fetchall():
            if current_group_no != cast(int, row[0]):
                if current_group:
                    result.append(frozenset(current_group))
                    current_group = []
                current_group_no = cast(int, row[0])
            current_group.append(row[1])
        cursor.close()
        if current_group:
            result.append(frozenset(current_group))
        return tuple(result)

    def iter_groups_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserGroup]:
        """Return an iterator of group data of some user."""
        cursor = self._execute(
            "SELECT grouping_key, name, group_no FROM groups,groupings "
            "WHERE user_key=? AND grouping_key=key",
            (user_key,))
        result = []
        for grouping_key, grouping_name, group_no in cursor.fetchall():
            cursor_2 = self._execute(
                "SELECT user_key, ident FROM groups,users "
                "WHERE grouping_key=? AND group_no=? AND user_key=key",
                (grouping_key, group_no))
            result.append(UserGroup(
                grouping_key, grouping_name,
                frozenset(NamedUser(*row) for row in cursor_2.fetchall())))
            cursor_2.close()
        cursor.close()
        return result


class SqliteMemoryConnection(SqliteConnection):
    """SQLite-based and memory-based connection."""

    def close(self, _success: bool):
        """Close the connection, but do not close the connection."""
        self._connection = None


REL_DICT = {
    "eq": "=?",
    "ne": "!=?",
    "lt": "<?",
    "le": "<=?",
    "gt": ">?",
    "ge": ">=?",
}
REL_NONE_DICT = {"eq": " IS NULL", "ne": " IS NOT NULL"}


def relop_clause(field: str, relop: str, value: Any, or_null: bool) -> Tuple[str, bool]:
    """Return correct relational operator."""
    if value is None:
        try:
            return field + REL_NONE_DICT[relop], False
        except KeyError:
            return "", False
    if or_null:
        return "(%s %s OR %s IS NULL)" % (field, REL_DICT[relop], field), True
    return field + REL_DICT[relop], True


def where_clause(
        where: Optional[WhereSpec],
        nullable_fields: Optional[AbstractSet[str]] = None,
        no_where: bool = False) -> Tuple[str, List[Any]]:
    """Transform where specification into SQL WHERE clause."""
    if not where:
        return "", []
    where_parts = []
    bindings = []
    for where_spec, where_val in where.items():
        if isinstance(where_val, Permissions):
            where_val = where_val.value
        where_field, where_relop = where_spec.split("__")
        relop, bind_val = relop_clause(
            where_field,
            where_relop,
            where_val,
            (where_field in nullable_fields) if nullable_fields else False)
        if relop:
            where_parts.append(relop)
            if bind_val:
                bindings.append(where_val)
    if where_parts:
        return (" AND " if no_where else " WHERE ") + \
            " AND ".join(where_parts), bindings
    return "", []


def order_clause(order: Optional[OrderSpec]) -> str:
    """Transform order specification into SQL ORDER clause."""
    if not order:
        return ""
    order_parts = []
    for field in order:
        reverse = False
        if field.startswith("-"):
            reverse = True
            field = field[1:]
        elif field.startswith("+"):
            field = field[1:]
        order_parts.append("%s %s" % (field, "DESC" if reverse else "ASC"))
    return " ORDER BY " + ", ".join(order_parts)
