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

import dataclasses
import json
from typing import Any, List, Optional, Sequence, Tuple, cast

from ..logic import len_groups, make_code
from ..models import Grouping, GroupingKey, UserKey, UserPreferences
from ..preferences import get_code, get_preferences
from ..utils import now
from .base import Connection, DuplicateKey


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


GroupingCount = Tuple[Grouping, int]


def groupings_for_host(
        connection: Connection,
        host_key: UserKey) -> Tuple[Sequence[GroupingCount], Sequence[Grouping]]:
    """
    Retunr sequence of open and closed groupings.

    Open grouping will have an additional number of reservations / groups size,
    closed grouping will only be listed.
    """
    yet = now()
    open_groupings = []
    closed_groupings: List[Grouping] = []
    for grouping in connection.iter_groupings(
            where={"host_key__eq": host_key},
            order=["final_date"]):
        if grouping.close_date is None or grouping.close_date >= yet:
            count = connection.count_registrations_by_grouping(
                cast(GroupingKey, grouping.key))
            if count == 0:
                count = len_groups(connection.get_groups(
                    cast(GroupingKey, grouping.key)))
            open_groupings.append((grouping, count))
        else:
            closed_groupings.append(grouping)
    return (open_groupings, closed_groupings)


def encode_preferences(preferences: UserPreferences) -> Optional[str]:
    """Translate preferences into some encoding."""
    code = get_code(preferences)
    if code is None:
        return None

    value_dict = {
        'code': code,
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
        preference_class = get_preferences(value_dict['code'])
        if preference_class is None:
            return None
        field_names = [field.name for field in dataclasses.fields(preference_class)]
        fields = value_dict['fields']
        values = [_list_to_tuple(fields[name]) for name in field_names]
        result = preference_class(*values)  # type: ignore
        return result
    except Exception:  # pylint: disable=broad-except
        return None
