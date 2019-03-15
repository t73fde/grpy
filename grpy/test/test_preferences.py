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

"""Test the registry for preferences."""

import dataclasses  # pylint: disable=wrong-import-order
from typing import Type, cast

from ..models import UserPreferences
from ..policies.preferred import PreferredPreferences
from ..policies.simple_belbin import SimpleBelbinPreferences
from ..preferences import get_code, get_preferences, register_preferences

_PREFERENCES_CLASSES = {
    UserPreferences, PreferredPreferences, SimpleBelbinPreferences,
}


def test_valid_preferences() -> None:
    """Test registry for known preferences."""
    for pref_class in _PREFERENCES_CLASSES:
        # Dirty trick to instantiate a preferences object
        field_names = [field.name for field in dataclasses.fields(pref_class)]
        code = get_code(pref_class(*field_names))

        assert code is not None
        preferences_class = get_preferences(code)
        assert pref_class == preferences_class


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class NoPreferences:
    """Test class for user preferences."""


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class UnregisteredPreferences(UserPreferences):
    """Test class for user preferences."""


def test_invalid_preferences() -> None:
    """Registry must return `None` for invalid preferences."""
    for obj in (1, None, NoPreferences, UnregisteredPreferences):
        assert get_code(cast(UserPreferences, obj)) is None


def test_invalid_code() -> None:
    """Registry must return `None` for invalid codes."""
    for code in (None, 1, "", NoPreferences, chr(0) * 4):
        assert get_preferences(cast(str, code)) is None


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class YetUnregisteredPreferences(UserPreferences):
    """Test class for user preferences."""


def test_register_preferences() -> None:
    """After registration, preferences and codes can be retrieved."""
    assert get_code(YetUnregisteredPreferences()) is None
    register_preferences('yetu', YetUnregisteredPreferences)
    assert get_code(YetUnregisteredPreferences()) == 'yetu'
    assert get_preferences('yetu') is YetUnregisteredPreferences


def test_invalid_registrations() -> None:
    """An already registered code / preferences doesn't alter anything."""
    up_code = get_code(UserPreferences())
    assert up_code is not None
    register_preferences('abcd', UserPreferences)
    assert get_code(UserPreferences()) == up_code
    assert get_preferences('abcd') is None

    register_preferences(up_code, UnregisteredPreferences)
    assert get_preferences(up_code) == UserPreferences

    register_preferences('wxyz', cast(Type[UserPreferences], NoPreferences))
    assert get_preferences('wxyz') is None
