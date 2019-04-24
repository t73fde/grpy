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

"""Web views for grpy."""

import dataclasses
import io
from typing import List, Sequence, cast

import pyqrcode
from flask import (abort, current_app, g, redirect, render_template, request,
                   url_for)

from .. import utils
from ..models import Grouping, GroupingKey, GroupingState
from ..repo.base import Connection
from ..repo.logic import GroupingCount, groupings_for_host
from .utils import redirect_to_login, value_or_404


def get_connection() -> Connection:
    """Return an open connection, specific for this request."""
    return cast(Connection, current_app.get_connection())


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class UserGroup:
    """A group for a given user, prepared for view."""

    grouping_key: GroupingKey
    grouping_name: str
    named_group: Sequence[str]


def home():
    """Show home page."""
    open_groupings: Sequence[GroupingCount] = []
    closed_groupings: Sequence[Grouping] = []
    registrations: List[Grouping] = []
    group_list: List[UserGroup] = []
    show_welcome = True
    if g.user:
        if g.user.is_host:
            open_groupings, closed_groupings = groupings_for_host(
                get_connection(), g.user.key)
            show_welcome = False

        group_list = []
        assigned_groupings = set()
        for group in get_connection().iter_groups_by_user(
                g.user.key,
                order=["grouping_name"]):
            if group.grouping_close_date is not None and \
                    group.grouping_close_date < utils.now():
                continue
            group_list.append(UserGroup(
                group.grouping_key,
                group.grouping_name,
                sorted(m.user_ident for m in group.group)))
            assigned_groupings.add(group.grouping_key)
        grouping_iterator = get_connection().iter_groupings_by_user(
            g.user.key,
            where={"close_date__ge": utils.now()},
            order=["final_date"])
        registrations = [
            grouping for grouping in grouping_iterator
            if grouping.key not in assigned_groupings]

        show_welcome = show_welcome and not (
            open_groupings or registrations or group_list)

    return render_template(
        "home.html",
        show_welcome=show_welcome, open_groupings=open_groupings,
        closed_groupings=closed_groupings,
        registrations=registrations, group_list=group_list)


def about():
    """Show about page."""
    return render_template("about.html", version=current_app.version.user_version)


def shortlink(code: str):
    """Show information for short link."""
    grouping = value_or_404(get_connection().get_grouping_by_code(code.upper()))
    if g.user is None:
        return redirect_to_login()

    state = get_connection().get_grouping_state(cast(GroupingKey, grouping.key))
    if state not in (GroupingState.NEW, GroupingState.AVAILABLE):
        abort(404)

    if g.user.key == grouping.host_key:
        url = request.url
        pos = url.find("?")
        if pos >= 0:
            url = url[:pos]
        qr_code = pyqrcode.create(url)
        byte_data = io.BytesIO()
        try:
            scale = max(2, int(request.args.get("scale", 8)))
        except ValueError:
            scale = 8
        qr_code.svg(byte_data, scale=scale, quiet_zone=2, xmldecl=False)
        return render_template(
            "grouping_code.html",
            code=grouping.code,
            url=url,
            qr_svg=byte_data.getbuffer().tobytes().decode("utf-8"))

    return redirect(url_for(
        'grouping.register', grouping_key=cast(GroupingKey, grouping.key)))
