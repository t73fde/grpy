
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

"""Policies for group forming."""

from typing import List, Tuple


POLICIES = [
    ('RD', "Random"),
]
POLICY_DICT = dict(POLICIES)


def get_policies() -> List[Tuple[str, str]]:
    """Return list of policies."""
    return list(POLICIES)


def get_policy_name(code: str) -> str:
    """Return policy name for given code."""
    return POLICY_DICT.get(code, "")
