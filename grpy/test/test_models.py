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

"""Test the models module."""

import dataclasses  # pylint: disable=wrong-import-order
from datetime import timedelta
from typing import cast

import pytest

from ..models import (Grouping, GroupingKey, GroupingState, Permissions,
                      Registration, User, UserKey, UserPreferences,
                      ValidationFailed)
from ..utils import now


def test_keytype_operations() -> None:
    """Test class methods of KeyType."""
    user_key = UserKey(int=0)
    grouping_key = GroupingKey(int=0)
    assert user_key != grouping_key
    assert UserKey() != user_key
    assert GroupingKey() != grouping_key
    assert UserKey(key=grouping_key) == user_key
    assert GroupingKey(key=user_key) == grouping_key


def test_user_is_host() -> None:
    """Test method .is_host."""
    assert User(None, "name", Permissions.HOST).is_host
    assert not User(None, "name").is_host


def test_user_validation() -> None:
    """A valid model raises no exception."""
    User(None, "name").validate()


def test_user_validation_failed() -> None:
    """An invalid model raises exception."""
    with pytest.raises(ValidationFailed, match="Key is not an UserKey"):
        User("123", "name").validate()  # type: ignore
    with pytest.raises(ValidationFailed, match="Ident is empty"):
        User(None, "").validate()


def test_grouping_validation() -> None:
    """A valid model raises no exception."""
    yet = now()
    delta = timedelta(seconds=1)
    Grouping(
        None, "code", "name", UserKey(int=0),
        yet, yet + delta, yet + delta + delta, "RD", 2, 0, "").validate()
    Grouping(
        GroupingKey(int=0), "code", "name", UserKey(int=0),
        yet, yet + delta, yet + delta + delta, "RD", 2, 0, "").validate()


def test_grouping_validation_failed() -> None:
    """An invalid model raises exception."""
    yet = now()
    delta = timedelta(seconds=1)
    with pytest.raises(ValidationFailed, match="Key is not a GroupingKey: "):
        Grouping(
            cast(GroupingKey, "123"), "code", "name", UserKey(int=0), yet,
            yet + delta, None, "RD", 2, 0, "").validate()
    with pytest.raises(ValidationFailed, match="Host is not an UserKey: "):
        Grouping(
            None, "code", "name", cast(UserKey, None), yet, yet + delta, None,
            "RD", 2, 0, "").validate()
    with pytest.raises(ValidationFailed, match="Code is empty: "):
        Grouping(
            None, "", "name", UserKey(int=0), yet, yet + delta, None,
            "RD", 2, 0, "").validate()
    with pytest.raises(ValidationFailed, match="Name is empty: "):
        Grouping(
            None, "code", "", UserKey(int=0), yet, yet + delta, None,
            "RD", 2, 0, "").validate()
    with pytest.raises(ValidationFailed, match="Begin date after final date: "):
        Grouping(
            None, "code", "name", UserKey(int=0), yet, yet, None,
            "RD", 2, 0, "").validate()
    with pytest.raises(ValidationFailed, match="Final date after close date: "):
        Grouping(
            None, "code", "name", UserKey(int=0), yet, yet + delta, yet + delta,
            "RD", 2, 0, "").validate()
    with pytest.raises(ValidationFailed, match="Policy is empty: "):
        Grouping(
            None, "code", "name", UserKey(int=0), yet, yet + delta, None,
            "", 2, 0, "").validate()
    with pytest.raises(ValidationFailed, match="Maximum group size < 1: 0"):
        Grouping(
            None, "code", "name", UserKey(int=0), yet, yet + delta, None,
            "RD", 0, 0, "").validate()
    with pytest.raises(ValidationFailed, match="Member reserve < 0: -1"):
        Grouping(
            None, "code", "name", UserKey(int=0), yet, yet + delta, None,
            "RD", 2, -1, "").validate()


def test_get_state() -> None:
    """Return valid date-based states."""
    yet = now()
    assert GroupingState.NEW == Grouping(
        None, ".", "name", UserKey(int=0), yet + timedelta(days=3),
        yet + timedelta(days=7), None, "RD", 7, 7, "").get_state()
    assert GroupingState.AVAILABLE == Grouping(
        None, ".", "name", UserKey(int=0), yet - timedelta(days=3),
        yet + timedelta(days=7), None, "RD", 7, 7, "").get_state()
    assert GroupingState.FINAL == Grouping(
        None, ".", "name", UserKey(int=0), yet - timedelta(days=3),
        yet - timedelta(days=2), None, "RD", 7, 7, "").get_state()
    assert GroupingState.FINAL == Grouping(
        None, ".", "name", UserKey(int=0), yet - timedelta(days=3),
        yet - timedelta(days=2), yet + timedelta(days=7), "RD", 7, 7, "").get_state()
    assert GroupingState.CLOSED == Grouping(
        None, ".", "name", UserKey(int=0), yet - timedelta(days=3),
        yet - timedelta(days=2), yet - timedelta(days=1), "RD", 7, 7, "").get_state()


def test_can_register() -> None:
    """User can register for Grouping."""
    yet = now()
    grouping = Grouping(
        None, ".", "name", UserKey(int=0), yet - timedelta(days=6),
        yet + timedelta(days=1), None, "RD", 7, 7, "Note")
    assert grouping.can_register()
    assert not dataclasses.replace(grouping, final_date=yet).can_register()


def test_registration_validation() -> None:
    """A valid model raises no exception."""
    Registration(GroupingKey(int=0), UserKey(int=0), UserPreferences()).validate()


def test_registration_validation_failed() -> None:
    """An invalid model raises exception."""
    with pytest.raises(ValidationFailed, match="Grouping is not a GroupingKey:"):
        Registration(
            cast(GroupingKey, None), UserKey(int=0), UserPreferences()).validate()
    with pytest.raises(ValidationFailed, match="Participant is not an UserKey:"):
        Registration(
            GroupingKey(int=0), cast(UserKey, None), UserPreferences()).validate()
    with pytest.raises(ValidationFailed, match="Preferences is not a UserPreferences"):
        Registration(
            GroupingKey(int=0), UserKey(int=0), cast(UserPreferences, "")).validate()
