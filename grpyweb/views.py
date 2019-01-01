
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

import datetime

from flask import current_app, flash, g, redirect, render_template, request, url_for

from grpydb.base import Repository


def get_repository() -> Repository:
    """Return an open repository, specific for this request."""
    return current_app.get_repository()


def home():
    """Show home page."""
    groupings = []
    if g.user:
        if g.user.is_host:
            groupings = get_repository().list_groupings(
                where={
                    "host__eq": g.user.key,
                    "close_date__leq": datetime.datetime.now()},
                order=["final_date"])
    return render_template("home.html", groupings=groupings)


def about():
    """Show about page."""
    return render_template("about.html")


def login():
    """Show login form and authenticate user."""
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


def grouping_detail(_key):
    """Show details of a grouping."""
