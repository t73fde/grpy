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

from ..check import ValidatingProxyRepository
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
    validate_proxy.set_user(User(None, "ident"))
    assert validate_proxy.mock.set_user.call_count == 1


def test_validate_set_grouping(
        validate_proxy: MockedValidatingProxyRepository, grouping: Grouping) -> None:
    """Add / update the given grouping."""
    validate_proxy.set_grouping(grouping)
    assert validate_proxy.mock.set_grouping.call_count == 1


def test_validate_set_registration(
        validate_proxy: MockedValidatingProxyRepository) -> None:
    """Add / update a grouping registration."""
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
