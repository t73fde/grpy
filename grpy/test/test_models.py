
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

"""Test the models module."""

import datetime
import uuid

import pytest

from ..models import Grouping, Permission, Registration, User, ValidationFailed
from ..utils import now


def test_user_is_host():
    """Test method .is_host."""
    assert User(None, "name", Permission.HOST).is_host
    assert not User(None, "name").is_host


def test_user_validation():
    """A valid model raises no exception."""
    User(None, "name").validate()


def test_user_validation_failed():
    """An invalid model raises exception."""
    with pytest.raises(ValidationFailed) as exc:
        User("123", "name").validate()
    assert "Key is not a UUID:" in str(exc)
    with pytest.raises(ValidationFailed) as exc:
        User(None, "").validate()
    assert "Ident is empty:" in str(exc)


def test_grouping_validation():
    """A valid model raises no exception."""
    yet = now()
    delta = datetime.timedelta(seconds=1)
    Grouping(
        None, "code", "name", uuid.UUID(int=0),
        yet, yet + delta, yet + delta + delta, "RD", 2, 0, "").validate()
    Grouping(
        uuid.UUID(int=0), "code", "name", uuid.UUID(int=0),
        yet, yet + delta, yet + delta + delta, "RD", 2, 0, "").validate()


def test_grouping_validation_failed():
    """An invalid model raises exception."""
    def assert_exc(grouping: Grouping, message: str) -> None:
        """Test for a specific exception message."""
        with pytest.raises(ValidationFailed) as exc:
            grouping.validate()
        assert message in str(exc)

    yet = now()
    delta = datetime.timedelta(seconds=1)
    assert_exc(Grouping(
        "123", "code", "name", uuid.UUID(int=0), yet, yet + delta, None,
        "RD", 2, 0, ""),
        "Key is not a UUID:")
    assert_exc(Grouping(
        None, "code", "name", None, yet, yet + delta, None, "RD", 2, 0, ""),
        "Host is not a UUID:")
    assert_exc(Grouping(
        None, "", "name", uuid.UUID(int=0), yet, yet + delta, None, "RD", 2, 0, ""),
        "Code is empty:")
    assert_exc(Grouping(
        None, "code", "", uuid.UUID(int=0), yet, yet + delta, None, "RD", 2, 0, ""),
        "Name is empty:")
    assert_exc(Grouping(
        None, "code", "name", uuid.UUID(int=0), yet, yet, None, "RD", 2, 0, ""),
        "Begin date after final date:")
    assert_exc(Grouping(
        None, "code", "name", uuid.UUID(int=0), yet, yet + delta, yet + delta,
        "RD", 2, 0, ""),
        "Final date after close date:")
    assert_exc(Grouping(
        None, "code", "name", uuid.UUID(int=0), yet, yet + delta, None,
        "", 2, 0, ""),
        "Policy is empty:")
    assert_exc(Grouping(
        None, "code", "name", uuid.UUID(int=0), yet, yet + delta, None,
        "RD", 0, 0, ""),
        "Maximal group size < 1:")
    assert_exc(Grouping(
        None, "code", "name", uuid.UUID(int=0), yet, yet + delta, None,
        "RD", 2, -1, ""),
        "Member reserve < 0:")


def test_registration_validation():
    """A valid model raises no exception."""
    Registration(uuid.UUID(int=0), uuid.UUID(int=0), "").validate()


def test_registration_validation_failed():
    """An invalid model raises exception."""
    with pytest.raises(ValidationFailed) as exc:
        Registration(None, uuid.UUID(int=0), "").validate()
    assert "Grouping is not a UUID:" in str(exc)
    with pytest.raises(ValidationFailed) as exc:
        Registration(uuid.UUID(int=0), None, "").validate()
    assert "Participant is not a UUID:" in str(exc)
