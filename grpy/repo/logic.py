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

from .base import DuplicateKey, Repository
from ..logic import make_code
from ..models import Grouping


def set_grouping_new_code(repository: Repository, grouping: Grouping) -> Grouping:
    """Set the short code of a grouping an store it in the repository."""
    counter = 0
    while counter < 100:
        try:
            return repository.set_grouping(
                grouping._replace(code=make_code(grouping, bool(counter))))
        except DuplicateKey as exc:
            if exc.args[0] != "Grouping.code":
                raise
        counter += 1
    raise OverflowError("grpy.repo.logic.set_grouping_new_code")
