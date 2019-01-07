
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
    abort, current_app, flash, g, redirect, render_template, url_for)

from . import forms
from .utils import value_or_404
from .. import utils
from ..models import User
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
                where={
                    "host__eq": g.user.key,
                    "close_date__le": utils.now()},
                order=["final_date"])
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

    form = forms.LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        if username and username[0] != "x":
            repository = get_repository()
            user = repository.get_user_by_username(username)
            if not user:
                user = repository.set_user(User(None, username))
            current_app.login(user)
            return redirect(url_for("home"))
        flash("Cannot authenticate user", category="error")
    else:
        print("NOFO", form.data, form.errors)
    return render_template("login.html", form=form)


def logout():
    """Logout current user."""
    current_app.logout()
    return redirect(url_for("home"))


def grouping_detail(key):
    """Show details of a grouping."""
    if not g.user:
        abort(401)
    grouping = value_or_404(get_repository().get_grouping(key))
    if g.user.key != grouping.host:
        abort(403)
    return render_template("grouping_detail.html", grouping=grouping)
