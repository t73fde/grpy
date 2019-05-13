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

"""Web views for grpy user management."""

import dataclasses
from typing import cast

from flask import (current_app, flash, g, redirect, render_template, request,
                   url_for)

from ...core.models import Permissions, User, UserKey
from ...repo.base import Connection, DuplicateKey
from ..utils import admin_required, value_or_404
from . import forms


def _get_user(user_key: UserKey) -> User:
    """
    Retrieve user with given key.

    Abort with HTTP code 404 if there is no such user.
    """
    return value_or_404(get_connection().get_user(user_key))


def get_connection() -> Connection:
    """Return an open connection, specific for this request."""
    return cast(Connection, current_app.get_connection())


@admin_required
def users():
    """Show the list of users."""
    user_list = get_connection().iter_users(order=['-last_login', 'ident'])
    return render_template("user_list.html", user_list=user_list)


@admin_required
def user_create():
    """Create a new user."""
    form = forms.UserForm()
    if form.validate_on_submit():
        ident = form.ident.data.strip()
        user = User(None, ident)
        try:
            user = get_connection().set_user(user)
            return redirect(url_for("user.detail", user_key=user.key))
        except DuplicateKey:
            flash("Ident '{}' is already in use.".format(ident), category="error")
    return render_template("user_create.html", form=form)


@admin_required
def user_detail(user_key: UserKey):
    """Show details of given user."""
    user = _get_user(user_key)
    is_other = user.key != g.user.key
    if request.method == 'POST':
        form = forms.UserPermissionsForm()
        if is_other:
            new_permissions = \
                Permissions(0) if form.active.data else Permissions.INACTIVE
            if form.admin.data:
                new_permissions |= Permissions.ADMIN
        else:
            # Current user cannot make himself inactive or non-admin
            new_permissions = Permissions.ADMIN
        if form.host.data:
            new_permissions |= Permissions.HOST
        if form.manager.data:
            new_permissions |= Permissions.MANAGER

        if user.permissions != new_permissions:
            get_connection().set_user(dataclasses.replace(
                user, permissions=new_permissions))
            flash("Permissions of '{}' updated.".format(user.ident), category="info")
        return redirect(url_for('user.users'))

    form = forms.UserPermissionsForm(data={
        'active': user.is_active,
        'host': user.is_host,
        'admin': user.is_admin})

    connection = get_connection()
    host_groupings = connection.iter_groupings(
        where={"host_key__eq": user_key}, order=["final_date"])
    user_groups = connection.iter_groups_by_user(
        user_key, order=["grouping_name"])
    user_keys = {group.grouping_key for group in user_groups}
    user_groupings = [
        grouping for grouping in
        connection.iter_groupings_by_user(user_key, order=["final_date"])
        if grouping.key not in user_keys]
    can_delete = not (host_groupings or user_groups or user_groupings)

    return render_template(
        "user_detail.html", user=user, form=form, is_other=is_other,
        host_groupings=host_groupings, user_groups=user_groups,
        user_groupings=user_groupings, can_delete=can_delete)


@admin_required
def user_delete(user_key: UserKey):
    """Delete the given user."""
    user = _get_user(user_key)
    detail_url = url_for('user.detail', user_key=user_key)
    if g.user.key == user_key:
        flash("You're not allowed to delete your own account.", category="warning")
        return redirect(detail_url)
    connection = get_connection()
    if connection.iter_groupings_by_user(user_key) or \
            connection.iter_groups_by_user(user_key) or \
            connection.iter_groupings(where={'host_key__eq': user_key}):
        flash("User is referenced by at least one grouping.", category="warning")
        return redirect(detail_url)

    connection.delete_user(user_key)
    flash("User '{}' deleted.".format(user.ident), category="info")
    return redirect(url_for('user.users'))
