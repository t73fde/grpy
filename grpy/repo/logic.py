
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

"""Repository logic."""

from .base import DuplicateKey, Repository
from ..logic import make_code
from ..models import Grouping


def set_grouping_new_code(repository: Repository, grouping: Grouping) -> Grouping:
    """Set the short code of a grouping an store it in the repository."""
    unique = False
    while True:
        try:
            return repository.set_grouping(
                grouping._replace(code=make_code(grouping, unique)))
        except DuplicateKey as exc:
            if exc.args[0] != "Grouping.code":
                raise
        unique = True


def registration_count(repository: Repository, grouping: Grouping) -> int:
    """Return the number of registrations for a given grouping."""
    return len(repository.iter_registrations(where={'grouping__eq': grouping.key}))
