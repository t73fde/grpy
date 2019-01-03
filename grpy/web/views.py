
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

"""Web views for grpy."""

from flask import (
    abort, current_app, flash, g, redirect, render_template, request, url_for)

from .. import utils
from ..repo.base import Repository


def get_repository() -> Repository:
    """Return an open repository, specific for this request."""
    return current_app.get_repository()


def home():
    """Show home page."""
    groupings = []
    if g.user:
        if g.user.is_host:
            groupings = get_repository().list_groupings(
                where_spec={
                    "host__eq": g.user.key,
                    "close_date__le": utils.now()},
                order_spec=["final_date"])
    return render_template("home.html", groupings=groupings)


def about():
    """Show about page."""
    return render_template("about.html")


def login():
    """Show login form and authenticate user."""
    if g.user:
        current_app.logout()
        flash("User '{}' was logged out.".format(g.user.username), category="info")
        g.user = None

    if request.method == "POST":
        username = request.form['username']
        user = get_repository().get_user_by_username(username)
        if current_app.login(user):
            return redirect(url_for("home"))
        flash("Cannot authenticate user", category="error")
    return render_template("login.html")


def logout():
    """Logout current user."""
    current_app.logout()
    return redirect(url_for("home"))


def grouping_detail(key):
    """Show details of a grouping."""
    if not g.user:
        abort(401)
    grouping = get_repository().get_grouping(key)
    if not grouping:
        abort(404)
    if g.user.key != grouping.host:
        abort(403)
    return render_template("grouping_detail.html", grouping=grouping)
