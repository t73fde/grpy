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

"""Repository logic."""

import dataclasses  # pylint: disable=wrong-import-order
import importlib
import json
from typing import Any, Optional, cast

from .base import Connection, DuplicateKey
from ..logic import make_code
from ..models import Grouping, UserPreferences


def set_grouping_new_code(connection: Connection, grouping: Grouping) -> Grouping:
    """Set the short code of a grouping an store it in the repository."""
    counter = 0
    while counter < 100:
        try:
            return connection.set_grouping(
                dataclasses.replace(grouping, code=make_code(grouping, bool(counter))))
        except DuplicateKey as exc:
            if exc.args[0] != "Grouping.code":
                raise
        counter += 1
    raise OverflowError("grpy.repo.logic.set_grouping_new_code")


def encode_preferences(preferences: UserPreferences) -> str:
    """Translate preferences into some encoding."""
    value_dict = {
        'type': [preferences.__class__.__module__, preferences.__class__.__name__],
        'fields': dataclasses.asdict(preferences),
    }
    json_str = json.dumps(value_dict)
    return json_str


def _list_to_tuple(value: Any) -> Any:
    """Translate a list into a tuple and leave other values unchanged."""
    if isinstance(value, list):
        return tuple(value)
    return value


def decode_preferences(encoded: str) -> Optional[UserPreferences]:
    """Reconstruct user preferences from encoding."""
    try:
        value_dict = json.loads(encoded)
        module_name, class_name = value_dict['type']
        module = importlib.import_module(module_name)
        preference_class = module.__dict__[class_name]
        if not issubclass(preference_class, UserPreferences):
            return None
        field_names = [field.name for field in dataclasses.fields(preference_class)]
        fields = value_dict['fields']
        values = [_list_to_tuple(fields[name]) for name in field_names]
        result = preference_class(*values)
        return cast(UserPreferences, result)
    except Exception:  # pylint: disable=broad-except
        return None
