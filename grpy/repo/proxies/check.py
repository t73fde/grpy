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

"""Checking proxy repositories."""


from .base import BaseProxyRepository
from ...models import (
    Grouping, GroupingKey, Groups, Registration, User, UserKey, ValidationFailed)


class ValidatingProxyRepository(BaseProxyRepository):
    """A repository that delegates all requests to a real repository."""

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        user.validate()
        return super().set_user(user)

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        grouping.validate()
        return super().set_grouping(grouping)

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        registration.validate()
        return super().set_registration(registration)

    def set_groups(self, grouping_key: GroupingKey, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        for group in groups:
            for member in group:
                if not isinstance(member, UserKey):
                    raise ValidationFailed(
                        "Group member is not an UserKey: " + repr(member))
        return super().set_groups(grouping_key, groups)
