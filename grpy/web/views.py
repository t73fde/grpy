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

from typing import NamedTuple, Sequence, cast

from flask import (
    abort, current_app, flash, g, redirect, render_template, request, url_for)

from . import forms
from .utils import (
    login_required, login_required_redirect, make_model, update_model,
    value_or_404)
from .. import logic, utils
from ..models import Grouping, KeyType, Registration, UserKey, UserPreferences
from ..policies import get_policy, get_policy_names
from ..repo.base import Repository
from ..repo.logic import set_grouping_new_code


def get_repository() -> Repository:
    """Return an open repository, specific for this request."""
    return cast(Repository, current_app.get_repository())


class UserGroup(NamedTuple):
    """A group for a given user, prepared for view."""

    grouping_key: KeyType  # --> models.grouping
    grouping_name: str
    named_group: Sequence[str]


def home():
    """Show home page."""
    groupings = registrations = group_list = []
    if g.user:
        if g.user.is_host:
            repository = get_repository()
            groupings = list(repository.iter_groupings(
                where={
                    "host_key__eq": g.user.key,
                    "close_date__ge": utils.now()},
                order=["final_date"]))
            counts = [
                repository.count_registrations_by_grouping(g.key) for g in groupings]
            groupings = zip(groupings, counts)

        group_list = []
        assigned_groupings = set()
        for group in get_repository().iter_groups_by_user(g.user.key):
            group_list.append(UserGroup(
                group.grouping_key,
                group.grouping_name,
                sorted(m.user_ident for m in group.group)))
            assigned_groupings.add(group.grouping_key)
        grouping_iterator = get_repository().iter_groupings_by_user(
            g.user.key,
            where={"close_date__ge": utils.now()},
            order=["final_date"])
        registrations = [
            grouping for grouping in grouping_iterator
            if grouping.key not in assigned_groupings]

    show_welcome = not groupings and not registrations and not group_list
    return render_template(
        "home.html",
        show_welcome=show_welcome,
        groupings=groupings, registrations=registrations, group_list=group_list)


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
    form.policy.choices = [('', '')] + get_policy_names()
    if form.validate_on_submit():
        grouping = make_model(
            Grouping, form.data, {"code": ".", "host_key": g.user.key})
        set_grouping_new_code(
            get_repository(), grouping._replace(code=logic.make_code(grouping)))
        return redirect(url_for("home"))
    return render_template("grouping_create.html", form=form)


@login_required
def grouping_detail(grouping_key):
    """Show details of a grouping."""
    grouping = value_or_404(get_repository().get_grouping(grouping_key))
    if g.user.key != grouping.host_key:
        abort(403)
    user_registrations = list(map(
        lambda r: r.user,
        get_repository().iter_user_registrations_by_grouping(grouping.key)))
    user_registrations.sort(key=lambda u: u.ident)

    form = forms.RemoveRegistrationsForm()
    if request.method == 'POST':
        delete_users = request.form.getlist('u')
        user_keys = {u.key for u in user_registrations}
        deleted_users = set()
        count = 0
        for user in delete_users:
            try:
                user_key = UserKey(user)
            except ValueError:
                continue
            if user_key in user_keys:
                get_repository().delete_registration(grouping.key, user_key)
                deleted_users.add(user_key)
                count += 1
        get_repository().set_groups(
            grouping.key,
            logic.remove_from_groups(
                get_repository().get_groups(grouping.key), deleted_users))
        flash("{} registered users removed.".format(count), category='info')
        return redirect(url_for('grouping_detail', grouping_key=grouping.key))

    can_delete = not user_registrations
    can_start = grouping.can_grouping_start() and user_registrations
    group_list = []
    for group in get_repository().get_groups(grouping.key):
        group_list.append(
            sorted(get_repository().get_user(member).ident for member in group))
    return render_template(
        "grouping_detail.html",
        grouping=grouping, group_list=group_list,
        user_registrations=user_registrations,
        can_delete=can_delete, can_start=can_start, form=form)


@login_required
def grouping_update(grouping_key):
    """Update an existing grouping."""
    grouping = value_or_404(get_repository().get_grouping(grouping_key))
    if g.user.key != grouping.host_key:
        abort(403)
    if request.method == 'POST':
        form = forms.GroupingForm()
    else:
        form = forms.GroupingForm(obj=grouping)
    form.policy.choices = get_policy_names()
    if form.validate_on_submit():
        grouping = update_model(grouping, form.data)
        get_repository().set_grouping(grouping)
        return redirect(url_for("home"))
    return render_template("grouping_update.html", form=form)


@login_required_redirect
def shortlink(code: str):
    """Show information for short link."""
    grouping = value_or_404(get_repository().get_grouping_by_code(code.upper()))
    if g.user.key == grouping.host_key:
        return render_template("grouping_code.html", code=grouping.code)

    return redirect(url_for('grouping_register', grouping_key=grouping.key))


@login_required
def grouping_register(grouping_key):
    """Register for a grouping."""
    grouping = value_or_404(get_repository().get_grouping(grouping_key))
    if g.user.key == grouping.host_key:
        abort(403)
    if not grouping.is_registration_open():
        flash("Not within the registration period for '{}'.".format(grouping.name),
              category="warning")
        return redirect(url_for('home'))
    registration = get_repository().get_registration(grouping.key, g.user.key)

    form = forms.RegistrationForm()
    if form.validate_on_submit():
        if form.submit_register.data:
            get_repository().set_registration(
                Registration(grouping.key, g.user.key, UserPreferences()))
            if registration:
                flash("Registration for '{}' is updated.".format(grouping.name),
                      category="info")
            else:
                flash("Registration for '{}' is stored.".format(grouping.name),
                      category="info")
        elif registration and form.submit_deregister.data:
            get_repository().delete_registration(
                registration.grouping_key, registration.user_key)
            flash("Registration for '{}' is removed.".format(grouping.name),
                  category="info")
        return redirect(url_for('home'))
    return render_template(
        "grouping_register.html",
        grouping=grouping, registration=registration, form=form)


@login_required
def grouping_start(grouping_key):
    """Start the grouping process."""
    grouping = value_or_404(get_repository().get_grouping(grouping_key))
    if g.user.key != grouping.host_key:
        abort(403)
    if not grouping.can_grouping_start():
        flash(
            "Grouping for '{}' must be after the final date.".format(
                grouping.name),
            category="warning")
        return redirect(url_for('home'))
    user_registrations = utils.LazyList(
        get_repository().iter_user_registrations_by_grouping(grouping.key))
    if not user_registrations:
        flash("No registrations for '{}' found.".format(grouping.name),
              category="warning")
        return redirect(url_for('grouping_detail', grouping_key=grouping.key))

    form = forms.StartGroupingForm()
    if form.validate_on_submit():
        policy_data = {u: p for (u, p) in user_registrations}
        policy = get_policy(grouping.policy)
        groups = policy(policy_data, grouping.max_group_size, grouping.member_reserve)
        get_repository().set_groups(grouping.key, groups)
        return redirect(url_for('grouping_detail', grouping_key=grouping.key))

    return render_template(
        "grouping_start.html",
        grouping=grouping, registration_count=len(user_registrations), form=form)
