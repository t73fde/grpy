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

"""A registry for preferences."""

from typing import Optional, Type

from .models import UserPreferences
from .policies.preferred import PreferredPreferences
from .policies.simple_belbin import SimpleBelbinPreferences


_CODE_TO_PREFERENCES = {
    'user': UserPreferences,
    'pref': PreferredPreferences,
    'sbel': SimpleBelbinPreferences,
}

_PREFERENCES_TO_CODE = {c: n for n, c in _CODE_TO_PREFERENCES.items()}


def get_preferences(code: str) -> Optional[Type[UserPreferences]]:
    """Return preferences class of given code, or `None`."""
    return _CODE_TO_PREFERENCES.get(code)


def get_code(preferences: UserPreferences) -> Optional[str]:
    """Return code of given preferences, or `None`."""
    return _PREFERENCES_TO_CODE.get(type(preferences))


def register_preferences(code: str, preferences_class: Type[UserPreferences]):
    """Register a new preferences class with given code."""
    if not issubclass(preferences_class, UserPreferences):
        return
    if get_preferences(code) is not None:
        return
    if _PREFERENCES_TO_CODE.get(preferences_class) is not None:
        return
    _CODE_TO_PREFERENCES[code] = preferences_class
    _PREFERENCES_TO_CODE[preferences_class] = code
