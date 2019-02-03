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

"""Some random utilities."""

import collections
from datetime import datetime
from typing import Deque, Iterator, TypeVar

from pytz import utc


def now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(tz=utc)


T = TypeVar("T")  # pylint: disable=invalid-name


class LazyList(Iterator[T]):
    """A list-like structure based on an iterator."""

    def __init__(self, iterator: Iterator[T]):
        """Initialize lazy list with an iterator."""
        self._iterator = (iterator)
        self._front: Deque[T] = collections.deque()

    def _consume(self) -> bool:
        """Move one element from iterator to front elements."""
        try:
            element = next(self._iterator)
        except StopIteration:
            return False
        self._front.append(element)
        return True

    def __bool__(self):
        """Treat it like a boolean."""
        if self._front:
            return True
        return self._consume()

    def __len__(self) -> int:
        """Return the length of the iterator."""
        while self._consume():
            pass
        return len(self._front)

    def __iter__(self):
        """Return itself to be an iterable."""
        return self

    def __next__(self):
        """Return the next element."""
        if self._front:
            return self._front.popleft()
        return next(self._iterator)
