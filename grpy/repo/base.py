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

"""Base definitions for repositories."""

from typing import Any, Dict, Iterable, NamedTuple, Optional, Sequence

from ..core.models import (Grouping, GroupingKey, Groups, Registration, User,
                           UserKey)
from .models import UserGroup, UserRegistration

WhereSpec = Dict[str, Any]
OrderSpec = Sequence[str]


class Message(NamedTuple):
    """A message to be delivered to a client."""

    category: str
    text: str
    exception: Optional[Exception] = None


class DuplicateKey(Exception):
    """Signal that a key is not unique."""


class NothingToUpdate(Exception):
    """Signal a missing data element, so that an update is not possible."""


class Connection:  # pylint: disable=too-many-public-methods
    """Abstract connection to a reposity."""

    def get_messages(self) -> Sequence[Message]:
        """Return all connection-related messages."""
        raise NotImplementedError("Connection.get_messages")

    def has_errors(self) -> bool:
        """Return True if some errors were detected with this connection."""
        raise NotImplementedError("Connection.has_errors")

    def close(self, success: bool) -> None:
        """Close the connection, store all permanent data."""
        raise NotImplementedError("Connection.close")

    def set_user(self, user: User) -> User:
        """Add / update the given user."""
        raise NotImplementedError("Connection.set_user")

    def get_user(self, user_key: UserKey) -> Optional[User]:
        """Return user for given primary key."""
        raise NotImplementedError("Connection.get_user")

    def get_user_by_ident(self, ident: str) -> Optional[User]:
        """Return user for given ident."""
        raise NotImplementedError("Connection.get_user_by_ident")

    def iter_users(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[User]:
        """
        Return an iterator of all or some users.

        If `where` is not None, only the users according to a specification are
        returned. The keys of `where` are composed of valid user attributes and
        a relation specification, separated by "__".  Relation specifications
        are one of: "eq", "ne", "ge", "gt", "lt", and "le".  Examples are:
        "ident__eq", "is_host__eq", "key__ne".  Please not: order relations,
        like "ge", "gt", "lt", "le" will always return True if compared with
        None. If you want to remove None values, explicitly add another element
        like `{"field__ne": None}`.

        If `order` is not None, the result is sorted with respect to given
        keys. Keys are valid user attributes, optionally prefixed by "-" or
        "+".  If the prefix "-" is given, sorting is descending, else it is
        ascending. Examples: "ident", "-ident".
        """
        raise NotImplementedError("Connection.iter_users")

    def set_grouping(self, grouping: Grouping) -> Grouping:
        """Add / update the given grouping."""
        raise NotImplementedError("Connection.set_grouping")

    def get_grouping(self, grouping_key: GroupingKey) -> Optional[Grouping]:
        """Return grouping with given key."""
        raise NotImplementedError("Connection.get_grouping")

    def get_grouping_by_code(self, code: str) -> Optional[Grouping]:
        """Return grouping with given short code."""
        raise NotImplementedError("Connection.get_grouping_by_code")

    def iter_groupings(
            self,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """
        Return an iterator of all or some groupings.

        See method `iter_users` for a detailed description of `where` and
        `order`.
        """
        raise NotImplementedError("Connection.iter_groupings")

    def delete_grouping(self, grouping_key: GroupingKey) -> None:
        """Delete the grouping object referenced by the given key."""
        raise NotImplementedError("Connection.delete_grouping")

    def set_registration(self, registration: Registration) -> Registration:
        """Add / update a grouping registration."""
        raise NotImplementedError("Connection.add_registration")

    def get_registration(
            self,
            grouping_key: GroupingKey, user_key: UserKey) -> Optional[Registration]:
        """Return registration with given grouping and user."""
        raise NotImplementedError("Connection.get_registration")

    def count_registrations_by_grouping(self, grouping_key: GroupingKey) -> int:
        """Return number of registration for given grouping."""
        raise NotImplementedError("Connection.count_registrations_by_grouping")

    def delete_registration(self, grouping_key: GroupingKey, user_key: UserKey) -> None:
        """Delete the given registration from the repository."""
        raise NotImplementedError("Connection.delete_registration")

    def delete_registrations(self, grouping_key: GroupingKey) -> None:
        """Delete all registrations of a grouping from the repository."""
        raise NotImplementedError("Connection.delete_registrations")

    def iter_groupings_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[Grouping]:
        """Return an iterator of all groupings the user applied to."""
        raise NotImplementedError("Connection.iter_groupings_by_user")

    def iter_user_registrations_by_grouping(
            self,
            grouping_key: GroupingKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserRegistration]:
        """Return an iterator of user data of some user."""
        raise NotImplementedError("Connection.iter_user_registrations_by_grouping")

    def set_groups(self, grouping_key: GroupingKey, groups: Groups) -> None:
        """Set / replace groups builded for grouping."""
        raise NotImplementedError("Connection.set_groups")

    def get_groups(self, grouping_key: GroupingKey) -> Groups:
        """Get groups builded for grouping."""
        raise NotImplementedError("Connection.get_groups")

    def iter_groups_by_user(
            self,
            user_key: UserKey,
            where: Optional[WhereSpec] = None,
            order: Optional[OrderSpec] = None) -> Iterable[UserGroup]:
        """Return an iterator of group data of some user."""
        raise NotImplementedError("Connection.iter_groups_by_user")


class Repository:
    """
    An abstract repository, i.e. a factory for connections.

    Every repository is initialized with a parsed URL that specifies the
    concrete data source, e.g. a database or a database management system. The
    type of this parsed URL is `str`.
    """

    def __init__(self, repository_url: str):
        """Initialize the repository with the URL."""
        self._url = repository_url

    @property
    def url(self) -> str:
        """Return the configured URL to access the data store."""
        return self._url

    def can_connect(self) -> bool:
        """Test the connection to the data store."""
        raise NotImplementedError("Repository.can_connect.")

    def initialize(self) -> bool:
        """Initialize the repository, if needed."""
        raise NotImplementedError("Repository.initialize.")

    def create(self) -> Connection:
        """Create and setup a connection."""
        raise NotImplementedError("Repository.create")
