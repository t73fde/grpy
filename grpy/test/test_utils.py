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

"""Test the utilities module."""

from datetime import timedelta, tzinfo
from typing import cast

from .. import utils
from ..utils import LazyList


def test_now() -> None:
    """The now functions returns an UTC timestamp."""
    now_tzinfo = cast(tzinfo, utils.now().tzinfo)
    assert now_tzinfo.utcoffset(None) == timedelta(0)
    assert now_tzinfo.tzname(None) == "UTC"


class MockIterator:
    """An iterator that counts how many its next method is called."""

    def __init__(self, max_count):
        """The next method can be called max_count."""
        self.max_count = max_count
        self.count = 0

    def __iter__(self):
        """This is an iterable too."""
        return self

    def __next__(self):
        """Return the next value."""
        if self.max_count <= self.count:
            raise StopIteration
        self.count += 1
        return self.count


def test_lazy_list_bool() -> None:
    """Test the lazy list as a boolean."""
    lazy: LazyList[int] = LazyList([])
    assert not lazy
    assert not bool(lazy)
    assert LazyList([1, 2, 3])
    assert not LazyList(i for i in [])  # type: ignore
    assert LazyList(i for i in [1])
    assert not LazyList(())
    assert LazyList((1,))
    assert not LazyList(MockIterator(0))

    mock_iterator = MockIterator(1)
    assert LazyList(mock_iterator)
    assert mock_iterator.count == 1

    mock_iterator = MockIterator(2)
    lazy = LazyList(mock_iterator)
    assert lazy
    assert bool(lazy)
    assert mock_iterator.count == 1


def test_lazy_list_len() -> None:
    """Calculating the length result in consuming the whole iterator."""
    assert len(LazyList([])) == 0  # pylint: disable=len-as-condition
    assert len(LazyList([1, 2, 3])) == 3
    assert len(LazyList(  # pylint: disable=len-as-condition
        i for i in [])) == 0  # type: ignore
    assert len(LazyList(i for i in [1])) == 1
    assert len(LazyList(())) == 0  # pylint: disable=len-as-condition
    assert len(LazyList((1,))) == 1

    for i in range(10):
        mock_iterator = MockIterator(i)
        assert len(LazyList(mock_iterator)) == i
        assert mock_iterator.count == i


def test_lazy_list_iterator() -> None:
    """The lazy list is itself an iterator."""
    assert list(LazyList([])) == []
    assert list(LazyList([1, 2, 3])) == [1, 2, 3]
    assert list(LazyList(i for i in [])) == []  # type: ignore
    assert list(LazyList(i for i in [1])) == [1]
    assert list(LazyList(())) == []
    assert list(LazyList((1,))) == [1]

    for i in range(10):
        mock_iterator = MockIterator(i)
        assert list(LazyList(mock_iterator)) == list(range(1, i + 1))
        assert mock_iterator.count == i


def test_lazy_list_bool_next() -> None:
    """Test combinations of bool and next function calls."""
    mock_iterator = MockIterator(7)
    lazy = LazyList(mock_iterator)
    assert bool(lazy)
    assert next(lazy) == 1
    assert mock_iterator.count == 1
    assert bool(lazy)
    assert mock_iterator.count == 2
    assert next(lazy) == 2
    assert mock_iterator.count == 2
    assert bool(lazy)
    assert mock_iterator.count == 3
    assert len(lazy) == 5
    assert mock_iterator.count == 7
