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

"""Web views for groupings."""

import dataclasses
from typing import List, cast

from flask import (abort, current_app, flash, g, redirect, render_template,
                   request, url_for)

from ... import logic, utils
from ...models import (Grouping, GroupingKey, GroupingState, Registration,
                       User, UserKey)
from ...policies import get_policy
from ...repo.base import Connection
from ...repo.logic import set_grouping_new_code
from ..policies import get_policy_names, get_registration_form
from ..utils import login_required, make_model, update_model, value_or_404
from . import forms


def get_connection() -> Connection:
    """Return an open connection, specific for this request."""
    return cast(Connection, current_app.get_connection())


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
            get_connection(),
            dataclasses.replace(grouping, code=logic.make_code(grouping)))
        return redirect(url_for("home"))
    return render_template("grouping_create.html", form=form)


def _get_grouping(grouping_key: GroupingKey) -> Grouping:
    """
    Retrieve grouping with given key.

    Abort with HTTP code 404 if there is no such grouping. Abort with HTTP code
    403 if the current user is not the host of the grouping.
    """
    grouping = value_or_404(get_connection().get_grouping(grouping_key))
    if g.user.key != grouping.host_key:
        abort(403)
    return grouping


@login_required
def grouping_detail(grouping_key: GroupingKey):
    """Show details of a grouping."""
    grouping = _get_grouping(grouping_key)

    user_registrations = list(map(
        lambda r: r.user,
        get_connection().iter_user_registrations_by_grouping(grouping_key)))
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
                get_connection().delete_registration(grouping_key, user_key)
                deleted_users.add(user_key)
                count += 1
        get_connection().set_groups(
            grouping_key,
            logic.remove_from_groups(
                get_connection().get_groups(grouping_key), deleted_users))
        flash("{} registered users removed.".format(count), category='info')
        return redirect(url_for('.detail', grouping_key=grouping_key))

    state = get_connection().get_grouping_state(grouping_key)
    group_list = _get_group_list(grouping_key)
    return render_template(
        "grouping_detail.html",
        grouping=grouping,
        group_list=group_list,
        user_registrations=user_registrations,
        can_show_link=state in (GroupingState.NEW, GroupingState.AVAILABLE),
        can_update=(state in (
            GroupingState.NEW, GroupingState.AVAILABLE, GroupingState.FINAL)),
        can_delete_regs=(state in (GroupingState.AVAILABLE, GroupingState.FINAL)),
        has_group=(state in (
            GroupingState.GROUPED, GroupingState.FASTENED, GroupingState.CLOSED)),
        is_grouped=(state == GroupingState.GROUPED),
        can_delete=(state in (GroupingState.NEW, GroupingState.CLOSED)),
        can_start=(state == GroupingState.FINAL),
        form=form)


def _get_group_list(grouping_key: GroupingKey) -> List[List[str]]:
    """Return a list of list of user idents, sorted by user ident."""
    # This could be a good candidate for a new repository method
    # (because of the many requests for the user idents)
    group_list = []
    for group in get_connection().get_groups(grouping_key):
        group_list.append(
            sorted(
                cast(User, get_connection().get_user(member)).ident
                for member in group))
    return group_list


@login_required
def grouping_update(grouping_key: GroupingKey):
    """Update an existing grouping."""
    grouping = _get_grouping(grouping_key)

    state = get_connection().get_grouping_state(grouping_key)
    if state not in (GroupingState.NEW, GroupingState.AVAILABLE, GroupingState.FINAL):
        flash("Update of grouping not allowed.", category='warning')
        return redirect(url_for('home'))

    if request.method == 'POST':
        form = forms.GroupingForm()
    else:
        form = forms.GroupingForm(obj=grouping)
    form.policy.choices = get_policy_names()
    if form.validate_on_submit():
        grouping = update_model(grouping, form.data)
        get_connection().set_grouping(grouping)
        return redirect(url_for("home"))
    return render_template("grouping_update.html", form=form)


@login_required
def grouping_register(grouping_key: GroupingKey):
    """Register for a grouping."""
    grouping = value_or_404(get_connection().get_grouping(grouping_key))
    if g.user.key == grouping.host_key:
        abort(403)

    if not grouping.can_register():
        flash("Grouping '{}' is not available.".format(grouping.name),
              category="warning")
        return redirect(url_for('home'))
    registration = get_connection().get_registration(grouping_key, g.user.key)

    form = get_registration_form(grouping.policy, registration)
    if form.validate_on_submit():
        user_preferences = form.get_user_preferences()
        get_connection().set_registration(
            Registration(grouping_key, g.user.key, user_preferences))
        if registration:
            flash("Registration for '{}' is updated.".format(grouping.name),
                  category="info")
        else:
            flash("Registration for '{}' is stored.".format(grouping.name),
                  category="info")
        return redirect(url_for('home'))
    form_template = getattr(form, "TEMPLATE", None)
    return render_template(
        "grouping_register.html",
        grouping=grouping, form=form, form_template=form_template)


@login_required
def grouping_start(grouping_key: GroupingKey):
    """Start the grouping process."""
    grouping = _get_grouping(grouping_key)

    state = get_connection().get_grouping_state(grouping_key)
    if state != GroupingState.FINAL:
        flash("Grouping is not final.", category="warning")
        return redirect(url_for('.detail', grouping_key=grouping_key))

    user_registrations = utils.LazyList(
        get_connection().iter_user_registrations_by_grouping(grouping_key))
    if not user_registrations:
        flash("No registrations for '{}' found.".format(grouping.name),
              category="warning")
        return redirect(url_for('.detail', grouping_key=grouping_key))

    form = forms.StartGroupingForm()
    if form.validate_on_submit():
        policy_data = {r.user: r.preferences for r in user_registrations}
        policy = get_policy(grouping.policy)
        groups = policy(policy_data, grouping.max_group_size, grouping.member_reserve)
        get_connection().set_groups(grouping_key, logic.sort_groups(groups))
        return redirect(url_for('.detail', grouping_key=grouping_key))

    return render_template(
        "grouping_start.html",
        grouping=grouping, registration_count=len(user_registrations), form=form)


@login_required
def grouping_remove_groups(grouping_key: GroupingKey):
    """Remove formed groups."""
    grouping = _get_grouping(grouping_key)

    state = get_connection().get_grouping_state(grouping_key)
    if state != GroupingState.GROUPED:
        flash("No groups to remove.", category="info")
        return redirect(url_for('.detail', grouping_key=grouping_key))

    form = forms.RemoveGroupsForm()
    if form.validate_on_submit():
        if form.submit_remove.data:
            get_connection().set_groups(grouping_key, ())
            flash("Groups removed.", category="info")
        return redirect(url_for('.detail', grouping_key=grouping_key))

    group_list = _get_group_list(grouping_key)
    return render_template(
        "grouping_remove_groups.html",
        grouping=grouping, group_list=group_list, form=form)


@login_required
def grouping_close(grouping_key: GroupingKey):
    """Set the close date of the grouping to now."""
    grouping = _get_grouping(grouping_key)

    if grouping.close_date:
        get_connection().set_grouping(dataclasses.replace(grouping, close_date=None))
        flash("Close date removed.", category="info")
    else:
        yet = utils.now()
        if yet <= grouping.final_date:
            flash("Please wait until final date is reached.", category="warning")
        else:
            get_connection().set_grouping(dataclasses.replace(
                grouping, close_date=yet))
            flash("Close date is now set.", category="info")
    return redirect(url_for('.detail', grouping_key=grouping.key))


@login_required
def grouping_fasten_groups(grouping_key: GroupingKey):
    """Fasten formed groups."""
    grouping = _get_grouping(grouping_key)

    state = get_connection().get_grouping_state(grouping_key)
    if state != GroupingState.GROUPED:
        flash("Grouping not performed recently.", category="warning")
        return redirect(url_for('.detail', grouping_key=grouping.key))

    form = forms.FastenGroupsForm()
    if form.validate_on_submit():
        if form.submit_fasten.data:
            get_connection().delete_registrations(grouping_key)
            flash("Groups fastened.", category="info")
        return redirect(url_for('.detail', grouping_key=grouping.key))

    group_list = _get_group_list(grouping_key)
    return render_template(
        "grouping_fasten.html",
        grouping=grouping, group_list=group_list, form=form)
