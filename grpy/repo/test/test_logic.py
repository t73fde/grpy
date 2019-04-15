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

"""Tests for the connection logic."""

import dataclasses
import datetime
from typing import Sequence, Tuple, cast
from unittest.mock import patch

import pytest

from ...models import Grouping, Registration, User, UserKey, UserPreferences
from ...preferences import get_code, register_preferences
from ..base import Connection, DuplicateKey
from ..logic import (decode_preferences, encode_preferences,
                     groupings_for_host, set_grouping_new_code)


def test_set_grouping_new_code(connection: Connection, grouping: Grouping) -> None:
    """Test the creation of new short code."""
    grouping_1 = set_grouping_new_code(connection, grouping)
    grouping_2 = set_grouping_new_code(connection, grouping)
    assert grouping_1.code != grouping_2.code


def test_set_grouping_new_code_db_error(
        connection: Connection, grouping: Grouping) -> None:
    """Test the creation of new short codes, some connection error occurs."""
    with patch.object(connection, "set_grouping") as func:
        func.side_effect = DuplicateKey("unknown")
        with pytest.raises(DuplicateKey):
            set_grouping_new_code(connection, grouping)


def test_set_grouping_new_code_no_random(
        connection: Connection, grouping: Grouping) -> None:
    """Test the creation of new short codes, if always the same code is made."""
    with patch.object(connection, "set_grouping") as func:
        func.side_effect = DuplicateKey("Grouping.code")
        with pytest.raises(
                OverflowError, match="grpy.repo.logic.set_grouping_new_code"):
            set_grouping_new_code(connection, grouping)


def test_groupings_for_host_none(connection: Connection, grouping: Grouping) -> None:
    """When no groupings are stored, both elements will be empty."""
    opened, closed = groupings_for_host(connection, grouping.host_key)
    assert opened == []
    assert closed == []


def make_users(connection: Connection, count: int) -> Sequence[User]:
    """Create some new user objects."""
    result = []
    for i in range(count):
        ident = "ident-%d" % i
        user = connection.get_user_by_ident(ident)
        if not user:
            user = connection.set_user(User(None, ident))
        result.append(user)
    return result


def test_groupings_for_host_opened_regs(
        connection: Connection, grouping: Grouping) -> None:
    """An open grouping with registrations will occur in first element."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None
    opened, closed = groupings_for_host(connection, grouping.host_key)
    assert len(opened) == 1
    assert opened[0][0] == grouping
    assert opened[0][1] == 0
    assert closed == []

    num_regs = 7
    for user in make_users(connection, num_regs):
        assert user.key is not None
        connection.set_registration(Registration(
            grouping.key, user.key, UserPreferences()))
    opened, closed = groupings_for_host(connection, grouping.host_key)
    assert len(opened) == 1
    assert opened[0][0] == grouping
    assert opened[0][1] == num_regs
    assert closed == []


def test_groupings_for_host_opened_groups(
        connection: Connection, grouping: Grouping) -> None:
    """An open grouping with registrations will occur in first element."""
    grouping = connection.set_grouping(grouping)
    assert grouping.key is not None

    num_regs = 9
    connection.set_groups(
        grouping.key,
        (frozenset(cast(UserKey, user.key) for user in make_users(
            connection, num_regs)),))
    opened, closed = groupings_for_host(connection, grouping.host_key)
    assert len(opened) == 1
    assert opened[0][0] == grouping
    assert opened[0][1] == num_regs
    assert closed == []


def test_groupings_for_host_closed(connection: Connection, grouping: Grouping) -> None:
    """A closed grouping is retrieved on the second element."""
    grouping = connection.set_grouping(dataclasses.replace(
        grouping,
        final_date=grouping.begin_date + datetime.timedelta(seconds=60),
        close_date=grouping.begin_date + datetime.timedelta(seconds=61)))

    opened, closed = groupings_for_host(
        connection, UserKey(int=grouping.host_key.int + 1))
    assert opened == []
    assert closed == []
    opened, closed = groupings_for_host(connection, grouping.host_key)
    assert opened == []
    assert closed == [grouping]


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class RealPreferences(UserPreferences):
    """Models some real preferences for other users."""

    favor: Tuple[str, ...]


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class PersonalityPreferences(UserPreferences):
    """Models result of a personality test."""

    openness: int
    shyness: int
    introvert: int


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class AnotherPersonalityPreferences(UserPreferences):
    """Models result of another personality test."""

    personality: Tuple[int, int, int, int]


register_preferences('tstr', RealPreferences)
register_preferences('tstp', PersonalityPreferences)
register_preferences('tsta', AnotherPersonalityPreferences)


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class NotPreferences(UserPreferences):
    """Not registered preferences."""


def test_preference_conversion() -> None:
    """Check that UserPreferences are converted to JSON and back."""

    assert encode_preferences(NotPreferences()) is None

    empty = UserPreferences()
    real = RealPreferences(("u1", "u2", "u3"))
    personality = PersonalityPreferences(4, 3, 11)
    personality_2 = AnotherPersonalityPreferences((2, 3, 5, 8))

    for preference in (empty, real, personality, personality_2):
        encoded = encode_preferences(preference)
        assert encoded is not None
        assert encoded != ""
        decoded = decode_preferences(encoded)
        assert decoded == preference


def test_decode_error() -> None:
    """Check for handle invalid data to be encoded gracefully."""
    assert decode_preferences("") is None
    assert decode_preferences("{}") is None
    assert decode_preferences('{"code": "abcxyz"}') is None
    code = get_code(RealPreferences(("u1", "u2", "u3")))
    assert code is not None
    assert decode_preferences(
        '{"code": "' + code + '", "fields": {"f": "V"}}') is None
