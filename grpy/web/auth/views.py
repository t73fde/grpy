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

from flask import (current_app, flash, g, redirect, render_template, request,
                   url_for)

from . import forms, logic


def login():
    """Show login form and authenticate user."""
    if g.user:
        current_app.logout()
        flash(f"User '{g.user.ident}' was logged out.", category="info")
        g.user = None

    if request.method == 'POST':
        form = forms.LoginForm()
        if form.validate():
            if logic.authenticate(form.ident.data, form.password.data):
                next_url = form.next_url.data
                if not next_url or not next_url.startswith("/"):
                    next_url = url_for('home')
                return redirect(next_url)
            flash("Cannot authenticate user", category="error")
    else:
        form = forms.LoginForm(data={'next_url': request.args.get('next_url', '')})
    return render_template("login.html", form=form)


def logout():
    """Logout current user."""
    current_app.logout()
    return redirect(url_for("home"))
