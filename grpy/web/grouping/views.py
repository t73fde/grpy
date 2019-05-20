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
import datetime
from typing import List, Optional, cast

from flask import (abort, current_app, flash, g, redirect, render_template,
                   request, url_for)

from ...core import logic, utils
from ...core.models import (Grouping, GroupingKey, GroupingState, Registration,
                            User, UserKey)
from ...policies import get_policy
from ...repo.base import Connection
from ...repo.logic import get_grouping_state, set_grouping_new_code
from ..policies import get_policy_names, get_registration_form
from ..utils import (admin_required, login_required, make_model, update_model,
                     value_or_404)
from . import forms


def get_connection() -> Connection:
    """Return an open connection, specific for this request."""
    return cast(Connection, current_app.get_connection())


def _redirect_to_detail(grouping_key: GroupingKey):
    """Redirect to detail page of given grouping."""
    return redirect(url_for('.detail', grouping_key=grouping_key))


def _can_delete(state: GroupingState) -> bool:
    """Return True if grouping can be deleted."""
    return state in (GroupingState.NEW, GroupingState.CLOSED)


def _can_set_final(state: GroupingState) -> bool:
    """Determine if final date can be set to current datetime."""
    return state in (GroupingState.AVAILABLE, GroupingState.FINAL)


def _can_set_close(grouping: Grouping) -> bool:
    """Determine if close date can be set to current datetime."""
    if grouping.close_date is not None:
        # Close date can be set to None
        return True
    return grouping.final_date < utils.now()


def _remove_groups(grouping_key: GroupingKey) -> None:
    """Remove all groups of this grouping."""
    get_connection().set_groups(grouping_key, ())


@dataclasses.dataclass(frozen=True)  # pylint: disable=too-few-public-methods
class GroupingData:
    """Some data about a grouping."""

    host_ident: str
    key: GroupingKey
    name: str
    final_date: datetime.datetime
    close_date: Optional[datetime.datetime]


@admin_required
def grouping_list():
    """Show list of all relevant groupings."""
    connection = get_connection()
    groupings = []
    for grouping in connection.iter_groupings():
        host = connection.get_user(grouping.host_key)
        groupings.append(GroupingData(
            host_ident=host.ident if host else "???",
            key=cast(GroupingKey, grouping.key),
            name=grouping.name,
            final_date=grouping.final_date,
            close_date=grouping.close_date))
    groupings.sort(key=lambda g: (g.host_ident, g.name, g.final_date))
    return render_template("grouping_list.html", groupings=groupings)


@login_required
def grouping_create():
    """Create a new grouping."""
    if not g.user.is_host:
        abort(403)
    form = forms.GroupingForm()
    form.policy.choices = [('', '')] + get_policy_names()
    if form.validate_on_submit():
        grouping = cast(Grouping, make_model(
            Grouping, form.data, {"code": ".", "host_key": g.user.key}))
        set_grouping_new_code(
            get_connection(),
            dataclasses.replace(grouping, code=logic.make_code(grouping)))
        return redirect(url_for("home"))
    return render_template("grouping_create.html", form=form)


def _get_grouping(grouping_key: GroupingKey, allow_admin: bool = False) -> Grouping:
    """
    Retrieve grouping with given key.

    Abort with HTTP code 404 if there is no such grouping. Abort with HTTP code
    403 if the current user is not the host of the grouping.
    """
    grouping = value_or_404(get_connection().get_grouping(grouping_key))
    if g.user.key != grouping.host_key:
        if not (allow_admin and g.user.is_admin):
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
    if form.is_submitted():
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
        flash(f"{count} registered users removed.", category="success")
        return _redirect_to_detail(grouping_key)

    state = get_grouping_state(get_connection(), grouping_key)
    group_list = _get_group_list(grouping_key)
    return render_template(
        "grouping_detail.html",
        grouping=grouping,
        group_list=group_list,
        user_registrations=user_registrations,
        can_show_link=state in (GroupingState.NEW, GroupingState.AVAILABLE),
        can_set_final=_can_set_final(state),
        can_set_close=_can_set_close(grouping),
        can_update=(state in (
            GroupingState.NEW, GroupingState.AVAILABLE, GroupingState.FINAL)),
        can_delete_regs=(state in (GroupingState.AVAILABLE, GroupingState.FINAL)),
        has_group=(state in (
            GroupingState.GROUPED, GroupingState.FASTENED, GroupingState.CLOSED)),
        is_grouped=(state == GroupingState.GROUPED),
        can_delete=_can_delete(state),
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

    state = get_grouping_state(get_connection(), grouping_key)
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
        return _redirect_to_detail(grouping_key)
    return render_template("grouping_update.html", form=form)


@login_required
def grouping_register(grouping_key: GroupingKey):
    """Register for a grouping."""
    grouping = value_or_404(get_connection().get_grouping(grouping_key))
    if g.user.key == grouping.host_key:
        abort(403)

    if not grouping.can_register():
        flash(f"Grouping '{grouping.name}' is not available.", category="warning")
        return redirect(url_for('home'))
    registration = get_connection().get_registration(grouping_key, g.user.key)

    form = get_registration_form(grouping.policy, registration)
    if form.validate_on_submit():
        user_preferences = form.get_user_preferences(current_app.config)
        get_connection().set_registration(
            Registration(grouping_key, g.user.key, user_preferences))
        if registration:
            flash(f"Registration for '{grouping.name}' is updated.", category="success")
        else:
            flash(f"Registration for '{grouping.name}' is stored.", category="success")
        return redirect(url_for('home'))
    form_template = getattr(form, "TEMPLATE", None)
    return render_template(
        "grouping_register.html",
        grouping=grouping, form=form, form_template=form_template)


@login_required
def grouping_start(grouping_key: GroupingKey):
    """Start the grouping process."""
    grouping = _get_grouping(grouping_key)

    state = get_grouping_state(get_connection(), grouping_key)
    if state != GroupingState.FINAL:
        flash("Grouping is not final.", category="warning")
        return _redirect_to_detail(grouping_key)

    user_registrations = utils.LazyList(
        get_connection().iter_user_registrations_by_grouping(grouping_key))
    if not user_registrations:
        flash(f"No registrations for '{grouping.name}' found.", category="warning")
        return _redirect_to_detail(grouping_key)

    form = forms.StartGroupingForm()
    if form.validate_on_submit():
        policy_data = {r.user: r.preferences for r in user_registrations}
        policy = get_policy(grouping.policy)
        groups = policy(policy_data, grouping.max_group_size, grouping.member_reserve)
        get_connection().set_groups(grouping_key, logic.sort_groups(groups))
        return _redirect_to_detail(grouping_key)

    return render_template(
        "grouping_start.html",
        grouping=grouping, registration_count=len(user_registrations), form=form)


@login_required
def grouping_remove_groups(grouping_key: GroupingKey):
    """Remove formed groups."""
    grouping = _get_grouping(grouping_key)

    state = get_grouping_state(get_connection(), grouping_key)
    if state != GroupingState.GROUPED:
        flash("No groups to remove.", category="info")
        return _redirect_to_detail(grouping_key)

    form = forms.RemoveGroupsForm()
    if form.validate_on_submit():
        if form.submit_remove.data:
            _remove_groups(grouping_key)
            flash("Groups removed.", category="success")
        return _redirect_to_detail(grouping_key)

    group_list = _get_group_list(grouping_key)
    return render_template(
        "grouping_remove_groups.html",
        grouping=grouping, group_list=group_list, form=form)


@login_required
def grouping_final(grouping_key: GroupingKey):
    """Set the final date of the grouping to now."""
    grouping = _get_grouping(grouping_key)
    state = get_grouping_state(get_connection(), grouping_key)
    if not _can_set_final(state):
        flash("Final date cannot be set now.", category="warning")
    else:
        get_connection().set_grouping(
            dataclasses.replace(grouping, final_date=utils.now()))
        flash("Final date is now set.", category="success")
    return _redirect_to_detail(grouping_key)


@login_required
def grouping_close(grouping_key: GroupingKey):
    """Set the close date of the grouping to now."""
    grouping = _get_grouping(grouping_key)
    if not _can_set_close(grouping):
        flash("Close date cannot be set now.", category="warning")
    elif grouping.close_date:
        get_connection().set_grouping(
            dataclasses.replace(grouping, close_date=None))
        flash("Close date removed.", category="success")
    else:
        get_connection().set_grouping(
            dataclasses.replace(grouping, close_date=utils.now()))
        flash("Close date is now set.", category="success")
    return _redirect_to_detail(grouping_key)


@login_required
def grouping_fasten_groups(grouping_key: GroupingKey):
    """Fasten formed groups."""
    grouping = _get_grouping(grouping_key)

    state = get_grouping_state(get_connection(), grouping_key)
    if state != GroupingState.GROUPED:
        flash("Grouping not performed recently.", category="warning")
        return _redirect_to_detail(grouping_key)

    form = forms.FastenGroupsForm()
    if form.validate_on_submit():
        if form.submit_fasten.data:
            get_connection().delete_registrations(grouping_key)
            flash("Groups fastened.", category="success")
        return _redirect_to_detail(grouping_key)

    group_list = _get_group_list(grouping_key)
    return render_template(
        "grouping_fasten.html",
        grouping=grouping, group_list=group_list, form=form)


@login_required
def grouping_assign(grouping_key: GroupingKey):
    """Assign grouping to another host."""
    grouping = _get_grouping(grouping_key, allow_admin=True)
    connection = get_connection()
    users = [
        user for user in connection.iter_users(order=["ident"]) if user.is_active]
    users.sort(key=lambda u: (not u.is_host, u.ident))
    form = forms.AssignGroupingForm()
    form.new_host.choices = [
        (cast(UserKey, user.key).hex, user.ident) for user in users]
    if form.is_submitted():
        if form.validate():
            # form.new_host.data must be a valid UUID hex value,
            # because of form validation.
            new_host_key = UserKey(form.new_host.data)
            new_host = connection.get_user(new_host_key)
            if new_host is not None:
                if new_host_key != grouping.host_key:
                    connection.set_grouping(dataclasses.replace(
                        grouping, host_key=new_host_key))
                    flash(f"Host of '{grouping.name}' is now '{new_host.ident}'.",
                          category="success")
            if form.next_url.data == "1":
                return redirect(url_for('.list'))
            return redirect(url_for('home'))
    else:
        form.new_host.data = grouping.host_key.hex
        if g.user.is_admin:
            form.next_url.data = "1"
    return render_template(
        "grouping_assign.html", grouping=grouping, form=form)


@login_required
def grouping_delete(grouping_key: GroupingKey):
    """Delete the grouping."""
    grouping = _get_grouping(grouping_key)

    state = get_grouping_state(get_connection(), grouping_key)
    if not _can_delete(state):
        flash("Grouping cannot be deleted.", category="warning")
        return _redirect_to_detail(grouping_key)

    form = forms.DeleteGroupingForm()
    if form.validate_on_submit():
        if form.submit_delete.data:
            _remove_groups(grouping_key)
            get_connection().delete_grouping(grouping_key)
            flash(f"Grouping '{grouping.name}' deleted.", category="success")
            return redirect(url_for('home'))
        return _redirect_to_detail(grouping_key)

    return render_template("grouping_delete.html", grouping=grouping, form=form)
