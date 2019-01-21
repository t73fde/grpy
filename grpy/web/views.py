
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

import uuid

from flask import (
    abort, current_app, flash, g, redirect, render_template, request, url_for)

from . import forms
from .utils import (
    login_required, login_required_redirect, make_model, update_model,
    value_or_404)
from .. import logic, utils
from ..models import Grouping, Registration
from ..policies import get_policies
from ..repo.base import Repository
from ..repo.logic import registration_count, set_grouping_new_code


def get_repository() -> Repository:
    """Return an open repository, specific for this request."""
    return current_app.get_repository()


def home():
    """Show home page."""
    groupings = registrations = []
    if g.user:
        if g.user.is_host:
            repository = get_repository()
            groupings = repository.iter_groupings(
                where={
                    "host__eq": g.user.key,
                    "close_date__ge": utils.now()},
                order=["final_date"])
            counts = [registration_count(repository, g) for g in groupings]
            groupings = zip(groupings, counts)

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
        flash("User '{}' was logged out.".format(g.user.ident), category="info")
        g.user = None

    if request.method == 'POST':
        form = forms.LoginForm()
    else:
        form = forms.LoginForm(data={'next_url': request.args.get('next_url', '')})

    if form.validate_on_submit():
        if current_app.authenticate(form.username.data, form.password.data):
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
            get_repository(), grouping._replace(code=logic.make_code(grouping)))
        return redirect(url_for("home"))
    return render_template("grouping_create.html", form=form)


@login_required
def grouping_detail(key):
    """Show details of a grouping."""
    grouping = value_or_404(get_repository().get_grouping(key))
    if g.user.key != grouping.host:
        abort(403)
    users = get_repository().iter_users_by_grouping(grouping.key, order=['ident'])
    form = forms.RemoveRegistrationsForm()
    if request.method == 'POST':
        delete_users = request.form.getlist('u')
        user_keys = {u.key for u in users}
        count = 0
        for user in delete_users:
            try:
                participant = uuid.UUID(user)
            except ValueError:
                continue
            if participant in user_keys:
                get_repository().delete_registration(grouping.key, participant)
                count += 1
        flash("{} registered users removed.".format(count), category='info')
        return redirect(url_for('grouping_detail', key=grouping.key))
    return render_template(
        "grouping_detail.html", grouping=grouping, users=users, form=form)


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
    if not logic.is_registration_open(grouping):
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
            get_repository().delete_registration(
                registration.grouping, registration.participant)
            flash("Registration for '{}' is removed.".format(grouping.name),
                  category="info")
        return redirect(url_for('home'))
    return render_template(
        "grouping_register.html",
        grouping=grouping, registration=registration, form=form)


@login_required
def grouping_start(key):
    """Start the grouping process."""
    grouping = value_or_404(get_repository().get_grouping(key))
    if g.user.key != grouping.host:
        abort(403)
    if not logic.can_grouping_start(grouping):
        flash(
            "Grouping for '{}' must be after the final date.".format(
                grouping.name),
            category="warning")
        return redirect(url_for('home'))
    registrations = get_repository().iter_registrations(
        where={'grouping__eq': grouping.key})
    if not registrations:
        flash("No registrations for '{}' found.".format(grouping.name),
              category="warning")
        return redirect(url_for('grouping_detail', key=grouping.key))

    form = forms.StartGroupingForm()
    if form.validate_on_submit():
        pass
    return render_template(
        "grouping_start.html",
        grouping=grouping, registrations=registrations, form=form)
