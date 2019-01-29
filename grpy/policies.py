
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

from typing import List, Sequence, Tuple

from .models import Groups, PolicyData


class Policy:
    """An abstract policy how to form groups."""

    NAME = ""

    @staticmethod
    def group_sizes(
            number_of_participants: int,
            max_group_size: int,
            member_reserve: int) -> Sequence[int]:
        """Return a vector of group sizes."""
        if number_of_participants < 0:
            raise ValueError("number_of_participants < 0: %d" % number_of_participants)
        if member_reserve < 0:
            raise ValueError("member_reserve < 0: %d" % member_reserve)
        potential_participants = number_of_participants + member_reserve
        if potential_participants <= 0:
            return []
        if max_group_size <= 0:
            raise ValueError("max_group_size <= 0: %d" % max_group_size)

        empty_groups = 0
        while member_reserve > max_group_size + 1:
            empty_groups += 1
            member_reserve -= max_group_size
            potential_participants -= max_group_size

        num_groups, remainder = divmod(potential_participants, max_group_size)
        if remainder > 0:
            num_groups += 1

        avg_group_size, remainder = divmod(number_of_participants, num_groups)
        groups = [avg_group_size + 1] * remainder + \
                 [avg_group_size] * (num_groups - remainder)
        return groups + [0] * empty_groups

    def build_groups(self, data: PolicyData) -> Groups:
        """Build a set of groups based on policy data."""
        raise NotImplementedError("Policy.build_groups")


class RandomPolicy(Policy):
    """Build groups randomly."""

    NAME = "Random"

    def build_groups(self, data: PolicyData) -> Groups:
        """Build a set of groups based on policy data."""


POLICIES = {
    'RD': RandomPolicy,
}


def get_policies() -> List[Tuple[str, str]]:
    """Return list of policies."""
    return [(code, policy.NAME) for code, policy in POLICIES.items()]


def get_policy_name(code: str) -> str:
    """Return policy name for given code."""
    policy = POLICIES.get(code)
    if policy:
        return policy.NAME
    return ""


def create_policy(code: str) -> Policy:
    """Create a policy object based on code."""
    return POLICIES.get(code)
