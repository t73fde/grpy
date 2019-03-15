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

"""Test specific for checking proxy connection."""

import dataclasses  # pylint: disable=wrong-import-order
import uuid
from typing import cast
from unittest.mock import Mock

import pytest

from ....models import (Grouping, GroupingKey, Registration, User, UserKey,
                        UserPreferences, ValidationFailed)
from ...base import DuplicateKey, Message, NothingToUpdate
from ..check import CatchingProxyConnection, ValidatingProxyConnection


class MockedValidatingProxyConnection(ValidatingProxyConnection):
    """A ProxyConnection that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


@pytest.fixture
def validate_proxy() -> MockedValidatingProxyConnection:
    """Set up a validating proxy connection."""
    delegate = Mock()
    delegate.return_value = 1017
    return MockedValidatingProxyConnection(delegate)


# pylint: disable=redefined-outer-name


def test_validate_set_user(validate_proxy: MockedValidatingProxyConnection) -> None:
    """Add / update the given user."""
    with pytest.raises(ValidationFailed, match="Ident is empty: "):
        validate_proxy.set_user(User(None, ""))
    assert validate_proxy.mock.set_user.call_count == 0

    validate_proxy.set_user(User(None, "."))
    assert validate_proxy.mock.set_user.call_count == 1


def test_validate_set_grouping(
        validate_proxy: MockedValidatingProxyConnection, grouping: Grouping) -> None:
    """Add / update the given grouping."""
    with pytest.raises(ValidationFailed, match="Maximum group size < 1: 0"):
        validate_proxy.set_grouping(dataclasses.replace(grouping, max_group_size=0))
    assert validate_proxy.mock.set_grouping.call_count == 0

    validate_proxy.set_grouping(grouping)
    assert validate_proxy.mock.set_grouping.call_count == 1


def test_validate_set_registration(
        validate_proxy: MockedValidatingProxyConnection) -> None:
    """Add / update a grouping registration."""
    with pytest.raises(ValidationFailed, match="Grouping is not a GroupingKey: 0"):
        validate_proxy.set_registration(
            Registration(cast(GroupingKey, 0), UserKey(int=0), UserPreferences()))
    assert validate_proxy.mock.set_registration.call_count == 0

    validate_proxy.set_registration(
        Registration(GroupingKey(int=0), UserKey(int=0), UserPreferences()))
    assert validate_proxy.mock.set_registration.call_count == 1


def test_validate_set_groups(validate_proxy: MockedValidatingProxyConnection) -> None:
    """Set / replace groups builded for grouping."""
    with pytest.raises(ValidationFailed, match="Group member is not an UserKey: None"):
        validate_proxy.set_groups(
            GroupingKey(int=0), (frozenset({cast(UserKey, None)}),))
    assert validate_proxy.mock.set_groups.call_count == 0
    with pytest.raises(
            ValidationFailed, match=r"Group member is not an UserKey: UUID\('"):
        validate_proxy.set_groups(
            GroupingKey(int=0), (frozenset({cast(UserKey, uuid.uuid4())}),))
    assert validate_proxy.mock.set_groups.call_count == 0
    with pytest.raises(
            ValidationFailed, match=r"Group member is not an UserKey: GroupingKey\('"):
        validate_proxy.set_groups(
            GroupingKey(int=0), (frozenset({cast(UserKey, GroupingKey())}),))
    assert validate_proxy.mock.set_groups.call_count == 0
    validate_proxy.set_groups(GroupingKey(int=0), (frozenset({UserKey(int=1)}),))
    assert validate_proxy.mock.set_groups.call_count == 1


# pylint: enable=redefined-outer-name


class MockedCatchProxyConnection(CatchingProxyConnection):
    """A ProxyConnection that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


@pytest.fixture
def catch_proxy() -> MockedCatchProxyConnection:
    """Set up a validating proxy connection."""
    delegate = Mock()
    delegate.return_value = 1017
    delegate.get_messages.return_value = [Message("test", "1017")]
    return MockedCatchProxyConnection(delegate)


# pylint: disable=redefined-outer-name


def test_catch_get_messages(catch_proxy: MockedCatchProxyConnection) -> None:
    """Return all connection-related messages."""
    catch_proxy.mock.set_user.side_effect = ValueError("BOOM!")
    catch_proxy.set_user(User(None, "name"))
    assert catch_proxy.get_messages()[0].text == \
        "Critical error: builtins.ValueError: BOOM!"
    assert catch_proxy.mock.get_messages.call_count == 1

    catch_proxy.get_messages(delete=True)
    assert catch_proxy.mock.get_messages.call_count == 2
    assert catch_proxy.get_messages() == [Message("test", "1017")]
    assert catch_proxy.mock.get_messages.call_count == 3

    catch_proxy.mock.get_messages.return_value = []
    assert catch_proxy.get_messages() == []
    assert catch_proxy.mock.get_messages.call_count == 4


def test_catch_set_user_excs(catch_proxy: MockedCatchProxyConnection) -> None:
    """Add / update the given user."""
    catch_proxy.mock.set_user.side_effect = DuplicateKey("User.ident", "123")
    catch_proxy.set_user(User(None, "ident"))
    assert catch_proxy.mock.set_user.call_count == 1
    assert catch_proxy.get_messages(delete=True)[0].text == \
        "Duplicate key for field 'User.ident' with value '123'"

    catch_proxy.mock.set_user.side_effect = NothingToUpdate("User.ident", "123")
    catch_proxy.set_user(User(None, "ident"))
    assert catch_proxy.mock.set_user.call_count == 2
    assert catch_proxy.get_messages(delete=True)[0].text == \
        "User.ident: try to update key 123"

    catch_proxy.mock.set_user.side_effect = ValidationFailed("User.ident")
    catch_proxy.set_user(User(None, "ident"))
    assert catch_proxy.mock.set_user.call_count == 3
    assert catch_proxy.get_messages(delete=True)[0].text == \
        "Internal validation failed: User.ident"


def test_catch_set_grouping_duplicate(
        catch_proxy: MockedCatchProxyConnection, grouping: Grouping) -> None:
    """Add / update the given grouping."""
    catch_proxy.mock.set_grouping.side_effect = DuplicateKey("Grouping.code", "123")
    with pytest.raises(DuplicateKey):
        catch_proxy.set_grouping(grouping)
    assert catch_proxy.mock.set_grouping.call_count == 1
