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

"""Web views for grpy.auth."""

from typing import cast

from flask import (current_app, flash, g, redirect, render_template, request,
                   url_for)

from ...core.models import User, UserKey
from ...repo.base import Connection
from ..utils import admin_required, value_or_404
from . import forms, logic


def _get_user(user_key: UserKey) -> User:
    """
    Retrieve user with given key.

    Abort with HTTP code 404 if there is no such user.
    """
    return value_or_404(get_connection().get_user(user_key))


def get_connection() -> Connection:
    """Return an open connection, specific for this request."""
    return cast(Connection, current_app.get_connection())


def login():
    """Show login form and authenticate user."""
    if g.user:
        current_app.logout()
        flash("User '{}' was logged out.".format(g.user.ident), category="info")
        g.user = None

    if request.method == 'POST':
        form = forms.LoginForm()
    else:
        form = forms.LoginForm(data={'next_url': request.args.get('next_url', '')})

    if form.validate_on_submit():
        if logic.authenticate(form.username.data, form.password.data):
            next_url = form.next_url.data
            if not next_url or not next_url.startswith("/"):
                next_url = url_for('home')
            return redirect(next_url)
        flash("Cannot authenticate user", category="error")
    return render_template("login.html", form=form)


def logout():
    """Logout current user."""
    current_app.logout()
    return redirect(url_for("home"))


@admin_required
def users():
    """Show the list of users."""
    user_list = get_connection().iter_users(order=['-last_login', 'ident'])
    return render_template("auth_users.html", user_list=user_list)


@admin_required
def user_detail(user_key: UserKey):
    """Show details of given user."""
    user = _get_user(user_key)
    return render_template("user_detail.html", user=user)
