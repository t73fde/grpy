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

"""Test specific for checking proxy repository."""

import uuid
from typing import cast
from unittest.mock import Mock

import pytest

from ..check import CatchingProxyRepository, ValidatingProxyRepository
from ...base import DuplicateKey, Message, NothingToUpdate
from ....models import (
    Grouping, GroupingKey, Registration, User, UserKey, UserPreferences,
    ValidationFailed)


class MockedValidatingProxyRepository(ValidatingProxyRepository):
    """A ProxyRepository that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


@pytest.fixture
def validate_proxy() -> MockedValidatingProxyRepository:
    """Set up a validating proxy repository."""
    delegate = Mock()
    delegate.return_value = 1017
    return MockedValidatingProxyRepository(delegate)


# pylint: disable=redefined-outer-name


def test_validate_set_user(validate_proxy: MockedValidatingProxyRepository) -> None:
    """Add / update the given user."""
    with pytest.raises(ValidationFailed, match="Ident is empty: "):
        validate_proxy.set_user(User(None, ""))
    assert validate_proxy.mock.set_user.call_count == 0

    validate_proxy.set_user(User(None, "."))
    assert validate_proxy.mock.set_user.call_count == 1


def test_validate_set_grouping(
        validate_proxy: MockedValidatingProxyRepository, grouping: Grouping) -> None:
    """Add / update the given grouping."""
    with pytest.raises(ValidationFailed, match="Maximum group size < 1: 0"):
        validate_proxy.set_grouping(grouping._replace(max_group_size=0))
    assert validate_proxy.mock.set_grouping.call_count == 0

    validate_proxy.set_grouping(grouping)
    assert validate_proxy.mock.set_grouping.call_count == 1


def test_validate_set_registration(
        validate_proxy: MockedValidatingProxyRepository) -> None:
    """Add / update a grouping registration."""
    with pytest.raises(ValidationFailed, match="Grouping is not a GroupingKey: 0"):
        validate_proxy.set_registration(
            Registration(cast(GroupingKey, 0), UserKey(int=0), UserPreferences()))
    assert validate_proxy.mock.set_registration.call_count == 0

    validate_proxy.set_registration(
        Registration(GroupingKey(int=0), UserKey(int=0), UserPreferences()))
    assert validate_proxy.mock.set_registration.call_count == 1


def test_validate_set_groups(validate_proxy: MockedValidatingProxyRepository) -> None:
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


class MockedCatchProxyRepository(CatchingProxyRepository):
    """A ProxyRepository that can be mocked."""

    @property
    def mock(self):
        """Return the delegate as a mock object."""
        return self._delegate


@pytest.fixture
def catch_proxy() -> MockedCatchProxyRepository:
    """Set up a validating proxy repository."""
    delegate = Mock()
    delegate.return_value = 1017
    delegate.get_messages.return_value = [Message("test", "1017")]
    return MockedCatchProxyRepository(delegate)


# pylint: disable=redefined-outer-name


def test_get_messages(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return all repository-related messages."""
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


def test_close(catch_proxy: MockedCatchProxyRepository) -> None:
    """Close the repository, store all permanent data."""
    catch_proxy.close(True)
    assert catch_proxy.mock.close.call_count == 1


def test_set_user(catch_proxy: MockedCatchProxyRepository) -> None:
    """Add / update the given user."""
    catch_proxy.set_user(User(None, "ident"))
    assert catch_proxy.mock.set_user.call_count == 1

    catch_proxy.mock.set_user.side_effect = DuplicateKey("User.ident", "123")
    catch_proxy.set_user(User(None, "ident"))
    assert catch_proxy.mock.set_user.call_count == 2
    assert catch_proxy.get_messages(delete=True)[0].text == \
        "Duplicate key for field 'User.ident' with value '123'"

    catch_proxy.mock.set_user.side_effect = NothingToUpdate("User.ident", "123")
    catch_proxy.set_user(User(None, "ident"))
    assert catch_proxy.mock.set_user.call_count == 3
    assert catch_proxy.get_messages(delete=True)[0].text == \
        "User.ident: try to update key 123"

    catch_proxy.mock.set_user.side_effect = ValidationFailed("User.ident")
    catch_proxy.set_user(User(None, "ident"))
    assert catch_proxy.mock.set_user.call_count == 4
    assert catch_proxy.get_messages(delete=True)[0].text == \
        "Internal validation failed: User.ident"


def test_get_user(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return user for given primary key."""
    catch_proxy.get_user(UserKey(int=0))
    assert catch_proxy.mock.get_user.call_count == 1


def test_get_user_by_ident(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return user for given ident."""
    catch_proxy.get_user_by_ident("")
    assert catch_proxy.mock.get_user_by_ident.call_count == 1


def test_iter_users(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return an iterator of all or some users."""
    catch_proxy.iter_users()
    assert catch_proxy.mock.iter_users.call_count == 1


def test_set_grouping(
        catch_proxy: MockedCatchProxyRepository, grouping: Grouping) -> None:
    """Add / update the given grouping."""
    catch_proxy.set_grouping(grouping)
    assert catch_proxy.mock.set_grouping.call_count == 1

    catch_proxy.mock.set_grouping.side_effect = DuplicateKey("Grouping.code", "123")
    with pytest.raises(DuplicateKey):
        catch_proxy.set_grouping(grouping)


def test_get_grouping(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return grouping with given key."""
    catch_proxy.get_grouping(GroupingKey(int=0))
    assert catch_proxy.mock.get_grouping.call_count == 1


def test_get_grouping_by_code(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return grouping with given short code."""
    catch_proxy.get_grouping_by_code("")
    assert catch_proxy.mock.get_grouping_by_code.call_count == 1


def test_iter_groupings(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return an iterator of all or some groupings."""
    catch_proxy.iter_groupings()
    assert catch_proxy.mock.iter_groupings.call_count == 1


def test_set_registration(catch_proxy: MockedCatchProxyRepository) -> None:
    """Add / update a grouping registration."""
    catch_proxy.set_registration(
        Registration(GroupingKey(int=0), UserKey(int=0), UserPreferences()))
    assert catch_proxy.mock.set_registration.call_count == 1


def test_get_registration(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return registration with given grouping and user."""
    catch_proxy.get_registration(GroupingKey(int=0), UserKey(int=1))
    assert catch_proxy.mock.get_registration.call_count == 1


def test_count_registrations_by_grouping(
        catch_proxy: MockedCatchProxyRepository) -> None:
    """Return number of registration for given grouping."""
    catch_proxy.count_registrations_by_grouping(GroupingKey(int=0))
    assert catch_proxy.mock.count_registrations_by_grouping.call_count == 1


def test_delete_registration(catch_proxy: MockedCatchProxyRepository) -> None:
    """Delete the given registration from the repository."""
    catch_proxy.delete_registration(GroupingKey(int=0), UserKey(int=1))
    assert catch_proxy.mock.delete_registration.call_count == 1


def test_iter_groupings_by_user(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return an iterator of all groupings the user applied to."""
    catch_proxy.iter_groupings_by_user(UserKey(int=0))
    assert catch_proxy.mock.iter_groupings_by_user.call_count == 1


def test_iter_user_registrations_by_grouping(
        catch_proxy: MockedCatchProxyRepository) -> None:
    """Return an iterator of user data of some user."""
    catch_proxy.iter_user_registrations_by_grouping(GroupingKey(int=0))
    assert catch_proxy.mock.iter_user_registrations_by_grouping.call_count == 1


def test_set_groups(catch_proxy: MockedCatchProxyRepository) -> None:
    """Set / replace groups builded for grouping."""
    catch_proxy.set_groups(GroupingKey(int=0), tuple(()))
    assert catch_proxy.mock.set_groups.call_count == 1


def test_get_groups(catch_proxy: MockedCatchProxyRepository) -> None:
    """Get groups builded for grouping."""
    catch_proxy.get_groups(GroupingKey(int=0))
    assert catch_proxy.mock.get_groups.call_count == 1


def test_iter_groups_by_user(catch_proxy: MockedCatchProxyRepository) -> None:
    """Return an iterator of group data of some user."""
    catch_proxy.iter_groups_by_user(UserKey(int=0))
    assert catch_proxy.mock.iter_groups_by_user.call_count == 1
