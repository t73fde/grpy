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

"""
Generic genetic algorithms to implement policies.

One remark to the '#nosec' comments: these are needed, because 'bandit' reports
an issue with theses statements: "Issue: [B311:blacklist] Standard
pseudo-random generators are not suitable for security/cryptographic
purposes.". But we need only some kind of randomness, not cryptographically
secure randomness. Therefore, the module 'random' is totally sufficient.
"""

import heapq
import random
import time
from typing import Any, Callable, Iterator, List, NamedTuple, Set, Tuple

from ..models import Groups, UserKey

Genome = List[List[UserKey]]
Rating = float
RatingFunc = Callable[[Genome, Any], Rating]


class RatedGenome(NamedTuple):
    """A rating together with its genome."""

    rating: Rating
    genome: Genome


Population = List[RatedGenome]


def build_genome(users: List[UserKey], sizes: List[int]) -> Genome:
    """Build new genome from list of users."""
    genome = []
    pos = 0
    for size in sizes:
        genome.append(users[pos:pos+size])
        pos += size
    return genome


def iter_genome_count(genome: Genome, count: int) -> Iterator[UserKey]:
    """Iterate over all members until number of member is reached."""
    for group in genome:
        for member in group:
            if count < 1:
                return
            yield member
            count -= 1


def iter_genome_set(genome: Genome, ignore_members: Set[UserKey]) -> Iterator[UserKey]:
    """Iterate over all members that will not be ignored."""
    for group in genome:
        for member in group:
            if member not in ignore_members:
                yield member


def crossover_genomes(
        genome_1: Genome, genome_2: Genome, user_count: int) -> Tuple[bool, Genome]:
    """Combine two genomes to a new one."""
    if genome_1 == genome_2 or len(genome_1) < 2:
        return (False, genome_1)
    split_pos = random.randint(1, user_count - 1)  # nosec
    users = list(iter_genome_count(genome_1, split_pos))
    users.extend(iter_genome_set(genome_2, set(users)))
    genome = build_genome(users, [len(group) for group in genome_1])
    return (True, genome)


def mutate_genome(genome: Genome) -> Genome:
    """Return a new genome value that is a permutation of the given one."""
    group_1 = random.randint(0, len(genome) - 1)  # nosec
    group_2 = random.randint(0, len(genome) - 1)  # nosec
    if group_1 == group_2:
        group_2 = (group_1 + 1) % len(genome)

    pos_1 = random.randint(0, len(genome[group_1]) - 1)  # nosec
    user_1 = genome[group_1][pos_1]
    pos_2 = random.randint(0, len(genome[group_2]) - 1)  # nosec
    user_2 = genome[group_2][pos_2]
    new_genome = []
    for number, group in enumerate(genome):
        if number == group_1:
            new_group = list(group)
            new_group[pos_1] = user_2
            new_genome.append(new_group)
        elif number == group_2:
            new_group = list(group)
            new_group[pos_2] = user_1
            new_genome.append(new_group)
        else:
            new_genome.append(group)
    return new_genome


def build_initial_population_genomes(
        population_size: int, users: List[UserKey], sizes: List[int]) -> List[Genome]:
    """Build an initial population of genomes."""
    user_list = list(users)
    result = []
    for _ in range(population_size):
        random.shuffle(user_list)
        result.append(build_genome(user_list, sizes))
    return result


def build_initial_population(
        population_size: int, users: List[UserKey], sizes: List[int],
        rating_func: RatingFunc, rating_data: Any) -> Population:
    """Build an initial population, ordered by rating."""
    genome_list = build_initial_population_genomes(population_size, users, sizes)
    population = [
        RatedGenome(rating_func(genome, rating_data), genome)
        for genome in genome_list]
    heapq.heapify(population)
    return population


def mutate_population(
        population: Population, num_mutation: int) -> List[Tuple[Genome, Rating]]:
    """Perform a number of mutations on given population."""
    result = []
    for _ in range(num_mutation):
        rated_genome = random.choice(population)  # nosec
        mutated_genome = mutate_genome(rated_genome.genome)
        result.append((mutated_genome, rated_genome.rating))
    return result


def crossover_population(
        population: Population, num_crossover: int, user_count: int) -> List[Genome]:
    """Perform a number of crossover operations on given population."""
    result = []
    for _ in range(num_crossover):
        parent_genomes = random.sample(population, 2)
        gave_birth, child_genome = crossover_genomes(
            parent_genomes[0].genome, parent_genomes[1].genome, user_count)
        if gave_birth:
            result.append(child_genome)
    return result


def reduce_population(population: Population, population_size: int) -> None:
    """Reduce the population to be of given size."""
    while len(population) > population_size:
        genome_1_pos = random.randint(0, len(population) - 1)  # nosec
        genome_2_pos = random.randint(0, len(population) - 1)  # nosec
        if genome_1_pos == genome_2_pos:
            continue

        if population[genome_1_pos].rating < population[genome_2_pos].rating:
            del population[genome_2_pos]
        else:
            del population[genome_1_pos]


def trivial_groups(users: List[UserKey], num_groups) -> Groups:
    """There is only one groups, so the result is the trivial one."""
    result = [frozenset(users)]
    while len(result) < num_groups:
        result.append(frozenset())
    return tuple(result)


def best_groups(population: Population, num_groups: int) -> Groups:
    """Select the best genome and produces resulting groups."""
    result = [frozenset(group) for group in population[0].genome]
    while len(result) < num_groups:
        result.append(frozenset())
    return tuple(result)


class StopStrategy:  # pylint: disable=too-many-instance-attributes
    """Encapsulate the descision when to stop the algorithm."""

    def __init__(
            self, initial_rating: float,
            max_rounds: int, max_best_rounds: int, max_seconds: float):
        """Initialize the object."""
        self.initial_rating: float = initial_rating
        self.max_rounds: int = max_rounds
        self.max_best_rounds: int = max_best_rounds
        self.max_seconds: float = max_seconds
        self.start()

    def start(self):
        """Signal that algorithm starts."""
        self.best_rating: float = self.initial_rating
        self.best_rounds: int = 0
        self.rounds: int = 0
        self.time_start: float = time.monotonic()

    def should_continue(self, rating: float) -> bool:
        """Return True if algorithm should continue its work."""
        self.rounds += 1
        if self.max_rounds <= self.rounds:
            return False
        if rating < self.best_rating:
            self.best_rating = rating  # pylint: disable=attribute-defined-outside-init
            self.best_rounds = 0  # pylint: disable=attribute-defined-outside-init
        else:
            self.best_rounds += 1
            if self.max_best_rounds < self.best_rounds:
                return False
        return (time.monotonic() - self.time_start) < self.max_seconds


def generic_genetic_policy(
        users: List[UserKey], sizes: List[int],
        rating_func: RatingFunc, rating_data: Any,
        stop_strategy: StopStrategy) -> Groups:
    """Calculate a group that suits the rating at best."""
    num_groups = len(sizes)
    while sizes[-1] < 1:
        sizes = sizes[:-1]
    if len(sizes) < 2:
        return trivial_groups(users, num_groups)

    population_size = min(100, len(sizes) * len(users) * 2)

    population = build_initial_population(
        population_size, users, sizes, rating_func, rating_data)

    num_crossover = len(users)
    num_mutation = len(users) + population_size

    stop_strategy.start()
    while stop_strategy.should_continue(population[0].rating):
        for genome in crossover_population(population, num_crossover, len(users)):
            population.append(RatedGenome(rating_func(genome, rating_data), genome))

        successful_mutations = 0
        for genome, old_rating in mutate_population(population, num_mutation):
            new_rating = rating_func(genome, rating_data)
            if new_rating < old_rating:
                successful_mutations += 1
            population.append(RatedGenome(new_rating, genome))

        reduce_population(population, population_size)
        heapq.heapify(population)

    return best_groups(population, num_groups)
