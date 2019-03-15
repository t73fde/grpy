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

"""Tests for the genetic algorithms for implementing policies."""

import random
from typing import List

from ...models import Groups, UserKey
from ..genetic import (Genome, StopStrategy, build_genome,
                       generic_genetic_policy, iter_genome_count,
                       iter_genome_set)


def userkeys(count: int) -> List[UserKey]:
    """Generate a number of UserKeys."""
    return [UserKey(int=256 + i) for i in range(count)]


def test_build_genome() -> None:
    """Genomes are based on user keys and a sizes array."""

    assert build_genome([], []) == []
    assert build_genome([], [4]) == [[]]
    assert build_genome(userkeys(0), []) == []
    assert build_genome(userkeys(4), []) == []
    assert build_genome(userkeys(4), [3]) == [userkeys(4)[:3]]

    users = userkeys(7)
    assert build_genome(users, [4, 4]) == [users[:4], users[4:]]


def test_iter_genome_count() -> None:
    """Iterating over a genome should return the prefix of the users list."""
    for i in (0, 1, 4, 7):
        assert list(iter_genome_count([], i)) == []
        users = userkeys(i)
        genome = build_genome(users, [4, 4])
        for j in range(i):
            assert list(iter_genome_count(genome, j)) == users[:j]


def test_iter_genome_set() -> None:
    """Iterator must not return some UserKeys."""
    users = userkeys(7)
    genome = build_genome(users, [4, 4])
    ignore = set([users[-2], users[-1]])
    assert list(iter_genome_set(genome, ignore)) == users[:-2]
    assert list(iter_genome_set(genome, set())) == users
    assert list(iter_genome_set(genome, set(users))) == []
    assert list(iter_genome_set([], ignore)) == []


def test_stop_strategy() -> None:
    """The stop strategy must fulfill some properties."""
    stop_strategy = StopStrategy(100, 10, 5, 0.5)
    assert stop_strategy.best_rounds == 0
    stop_strategy.start()
    assert stop_strategy.rounds == 0
    for i in range(9):
        assert stop_strategy.should_continue(100 - i)
        assert stop_strategy.rounds == i + 1
    assert stop_strategy.rounds == 9
    assert stop_strategy.best_rounds == 0
    assert not stop_strategy.should_continue(80)
    assert stop_strategy.rounds == 10


def rating_func(genome: Genome, _data) -> float:
    """Simple rating function."""
    max_id = 256
    rating = 0.0
    for group in genome:
        max_id += len(group)
        for member in group:
            if max_id < member.int:
                rating += 1.0
    return rating


def assert_best_groups(user_count: int, sizes: List[int]) -> Groups:
    """Check a specific group configuration and return best solution."""
    stop_strategy = StopStrategy(1000000, 500, 50, 0.5)
    best_groups = generic_genetic_policy(
        userkeys(user_count), sizes, rating_func, None, stop_strategy)
    assert len(best_groups) == len(sizes)
    for group, size in zip(best_groups, sizes):
        assert len(group) <= size
    return best_groups


def test_genetic_simple() -> None:
    """Test some simple edge cases."""
    assert_best_groups(4, [6])
    assert_best_groups(1, [1, 0])
    assert_best_groups(5, [3, 2, 0])


def test_genetic() -> None:
    """Real test of genetic algorithm."""
    random.seed(13)
    assert_best_groups(70, [6, 6, 6, 6, 6, 5, 5, 5, 5, 5, 5, 5, 5])


def test_random_genetic() -> None:
    """Genetic algorithm can implement random policy."""
    stop_strategy = StopStrategy(0, 1, 0, 0.5)
    best_groups = generic_genetic_policy(
        userkeys(9), [4, 5], lambda group, data: 0, None, stop_strategy)
    assert len(best_groups) == 2
    assert len(best_groups[0]) == 4
    assert len(best_groups[1]) == 5
    assert stop_strategy.rounds == 1
