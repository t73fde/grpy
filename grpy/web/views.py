
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

from . import forms
from .utils import (
    login_required, login_required_redirect, make_model, update_model,
    value_or_404)
from .. import utils
from ..logic import is_registration_open, make_code
from ..models import Grouping, Registration, User
from ..policies import get_policies
from ..repo.base import Repository
from ..repo.logic import set_grouping_new_code


def get_repository() -> Repository:
    """Return an open repository, specific for this request."""
    return current_app.get_repository()


def home():
    """Show home page."""
    groupings = registrations = []
    if g.user:
        if g.user.is_host:
            groupings = get_repository().iter_groupings(
                where={
                    "host__eq": g.user.key,
                    "close_date__ge": utils.now()},
                order=["final_date"])

        registrations = get_repository().iter_groupings_by_participant(
            g.user.key,
            where={"close_date__ge": utils.now()},
            order=["final_date"])
    return render_template(
        "home.html", groupings=groupings, registrations=registrations)


def about():
    """Show about page."""
    return render_template("about.html")


def login():
    """Show login form and authenticate user."""
    if g.user:
        current_app.logout()
        flash("User '{}' was logged out.".format(g.user.username), category="info")
        g.user = None

    if request.method == 'POST':
        form = forms.LoginForm()
    else:
        form = forms.LoginForm(data={'next_url': request.args.get('next_url', '')})

    if form.validate_on_submit():
        username = form.username.data
        if username and username[0] != "x":
            repository = get_repository()
            user = repository.get_user_by_username(username)
            if not user:
                user = repository.set_user(User(None, username))
            current_app.login(user)
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


@login_required
def grouping_create():
    """Create a new grouping."""
    if not g.user.is_host:
        abort(403)
    form = forms.GroupingForm()
    form.policy.choices = [('', '')] + get_policies()
    if form.validate_on_submit():
        grouping = make_model(
            Grouping, form.data, {"code": ".", "host": g.user.key})
        set_grouping_new_code(
            get_repository(), grouping._replace(code=make_code(grouping)))
        return redirect(url_for("home"))
    return render_template("grouping_create.html", form=form)


@login_required
def grouping_detail(key):
    """Show details of a grouping."""
    grouping = value_or_404(get_repository().get_grouping(key))
    if g.user.key != grouping.host:
        abort(403)
    return render_template("grouping_detail.html", grouping=grouping)


@login_required
def grouping_update(key):
    """Update an existing grouping."""
    grouping = value_or_404(get_repository().get_grouping(key))
    if g.user.key != grouping.host:
        abort(403)
    if request.method == 'POST':
        form = forms.GroupingForm()
    else:
        form = forms.GroupingForm(obj=grouping)
    form.policy.choices = get_policies()
    if form.validate_on_submit():
        grouping = update_model(grouping, form.data)
        get_repository().set_grouping(grouping)
        return redirect(url_for("home"))
    return render_template("grouping_update.html", form=form)


@login_required_redirect
def shortlink(code: str):
    """Show information for short link."""
    grouping = value_or_404(get_repository().get_grouping_by_code(code.upper()))
    if g.user.key == grouping.host:
        return render_template("grouping_code.html", code=grouping.code)

    return redirect(url_for('grouping_register', key=grouping.key))


@login_required
def grouping_register(key):
    """Register for a grouping."""
    grouping = value_or_404(get_repository().get_grouping(key))
    if g.user.key == grouping.host:
        abort(403)
    if not is_registration_open(grouping):
        flash("Not within the registration period for '{}'.".format(grouping.name),
              category="warning")
        return redirect(url_for('home'))
    registration = get_repository().get_registration(grouping.key, g.user.key)

    form = forms.RegistrationForm()
    if form.validate_on_submit():
        if form.submit_register.data:
            get_repository().set_registration(
                Registration(grouping.key, g.user.key, ''))
            if registration:
                flash("Registration for '{}' is updated.".format(grouping.name),
                      category="info")
            else:
                flash("Registration for '{}' is stored.".format(grouping.name),
                      category="info")
        elif registration and form.submit_deregister.data:
            get_repository().delete_registration(registration)
            flash("Registration for '{}' is removed.".format(grouping.name),
                  category="info")
        return redirect(url_for('home'))
    return render_template(
        "grouping_register.html",
        grouping=grouping, registration=registration, form=form)
