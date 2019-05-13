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

"""Test the web views for auth blueprint."""

import dataclasses
import itertools
from typing import cast

from flask import url_for

from ....core.models import (Grouping, Permissions, Registration, User,
                             UserKey, UserPreferences)
from ...app import GrpyApp
from ...test.common import (check_bad_anon_requests, check_flash, check_get,
                            check_get_data, check_message, check_redirect,
                            check_requests)


def check_bad_requests(client, auth, url: str, do_post: bool = True) -> None:
    """Assert that others cannot access resource."""
    auth.login('user')
    check_requests(client, url, 403, do_post)
    auth.login('host')
    check_requests(client, url, 403, do_post)
    auth.login('manager')
    check_requests(client, url, 403, do_post)
    check_bad_anon_requests(client, auth, url, do_post)


def test_admin_users(app: GrpyApp, client, auth) -> None:
    """Only an admistrator is allowed to get this page."""
    url = url_for('user.users')
    check_bad_requests(client, auth, url, False)

    auth.login("admin")
    data = check_get_data(client, url)
    assert url in data
    for user in app.get_connection().iter_users():
        assert str(user.key) in data
        assert user.ident in data


def test_admin_user_create(app: GrpyApp, client, auth) -> None:
    """Test the creation of new users."""
    url = url_for('user.create')
    check_bad_requests(client, auth, url)

    auth.login('admin')
    check_get(client, url)

    response = client.post(url, data={})
    assert response.status_code == 200
    assert response.data.count(b'This field is required') == 1

    response = client.post(url, data={'ident': "name3"})
    user = app.get_connection().get_user_by_ident("name3")
    assert user is not None
    assert user.permissions == Permissions(0)
    assert user.last_login is None
    check_redirect(response, url_for('user.detail', user_key=user.key))

    response = client.post(url, data={'ident': "name3"})
    assert response.status_code == 200
    check_message(client, "error", "Ident 'name3' is already in use.")


def test_admin_user_detail(app: GrpyApp, client, auth) -> None:
    """Only an administrator is allowed to read all user details."""
    admin_user = app.get_connection().get_user_by_ident("admin")
    assert admin_user is not None
    assert admin_user.key is not None

    for user in app.get_connection().iter_users():
        url = url_for('user.detail', user_key=user.key)
        check_bad_requests(client, auth, url, False)
        auth.login("admin")
        data = check_get_data(client, url)
        assert "User " + user.ident in data
        if user.key == admin_user.key:
            assert " (You)" in data


def test_admin_change_permission(app: GrpyApp, client, auth) -> None:
    """An administrator can change permissions."""
    admin_user = app.get_connection().get_user_by_ident("admin")
    assert admin_user is not None
    assert admin_user.key is not None

    userlist_url = url_for('user.users')
    auth.login("admin")
    for user in app.get_connection().iter_users():
        assert user.key is not None
        url = url_for('user.detail', user_key=user.key)
        data = check_get_data(client, url)
        if user.key == admin_user.key:
            assert "Active" not in data
            assert "Administrator" not in data
        else:
            assert "Active" in data
            assert "Administrator" in data
        assert "Host" in data
        assert "Manager" in data

        for is_active, is_host, is_manager, is_admin in itertools.product(
                (True, False), repeat=4):
            response = client.post(url, data={
                'active': "y" if is_active else "",
                'host': "y" if is_host else "",
                'manager': "y" if is_manager else "",
                'admin': "y" if is_admin else "",
            })
            if user.key != admin_user.key:
                check_flash(
                    client, response, userlist_url,
                    "success", "Permissions of '{}' updated.".format(user.ident))
            new_user = app.get_connection().get_user(user.key)
            assert new_user is not None
            if user.key == admin_user.key:
                assert new_user.is_active
                assert new_user.is_admin
            else:
                assert new_user.is_active == is_active
                assert new_user.is_admin == is_admin
            assert new_user.is_host == is_host
            assert new_user.is_manager == is_manager

    # If no change was done, no flash will be displayed
    client.post(url, data=dict(active="y", host="y", admin="y"))
    client.get(url_for('home'))
    assert check_redirect(
        client.post(url, data=dict(active="y", host="y", admin="y")), userlist_url)


def test_admin_user_detail_lists(
        app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Show that all user details are displayed."""
    assert app_grouping.key is not None
    users = [
        app.get_connection().set_user(User(None, "user-%d" % i)) for i in range(5)]
    assert users[0].key is not None
    url = url_for('user.detail', user_key=users[0].key)
    auth.login("admin")

    data = check_get_data(client, url)
    assert "Delete User" in data
    assert "Hosted Groupings" not in data
    assert "Groups" not in data
    assert "Registered Groupings" not in data
    assert app_grouping.name not in data

    app.get_connection().set_registration(Registration(
        app_grouping.key, users[0].key, UserPreferences()))
    data = check_get_data(client, url)
    assert "Delete User" not in data
    assert "Hosted Groupings" not in data
    assert "Groups" not in data
    assert "Registered Groupings" in data
    assert app_grouping.name in data

    app.get_connection().set_groups(
        app_grouping.key, (frozenset([cast(UserKey, user.key) for user in users]),))
    data = check_get_data(client, url)
    assert "Delete User" not in data
    assert "Hosted Groupings" not in data
    assert "Groups" in data
    assert "Registered Groupings" not in data
    assert app_grouping.name in data
    for user in users:
        assert user.ident in data

    app.get_connection().set_groups(app_grouping.key, ())
    app.get_connection().delete_registrations(app_grouping.key)
    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping, host_key=users[0].key))
    data = check_get_data(client, url)
    assert "Delete User" not in data
    assert "Hosted Groupings" in data
    assert "Groups" not in data
    assert "Registered Groupings" not in data
    assert app_grouping.name in data


def check_has_groupings(client, delete_url: str, location_url: str) -> None:
    """Ensure that user cannot be deleted because of groupings."""
    assert check_flash(
        client, client.post(delete_url), location_url,
        "warning", "User is referenced by at least one grouping.")


def test_admin_user_delete(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Only an administrator is allowed to delete users (except itself)."""
    assert app_grouping.key is not None
    admin_user = app.get_connection().get_user_by_ident("admin")
    assert admin_user is not None
    assert admin_user.key is not None
    admin_url = url_for('user.delete', user_key=admin_user.key)

    assert client.get(admin_url).status_code == 405
    assert client.post(admin_url).status_code == 401
    auth.login("user")
    assert client.get(admin_url).status_code == 405
    assert client.post(admin_url).status_code == 403
    auth.login("host")
    assert client.get(admin_url).status_code == 405
    assert client.post(admin_url).status_code == 403
    auth.login("manager")
    assert client.get(admin_url).status_code == 405
    assert client.post(admin_url).status_code == 403

    auth.login("admin")
    assert client.get(admin_url).status_code == 405
    assert check_flash(
        client, client.post(admin_url),
        url_for('user.detail', user_key=admin_user.key),
        "warning", "You're not allowed to delete your own account.")

    user = app.get_connection().get_user_by_ident("user")
    assert user is not None
    assert user.key is not None
    url = url_for('user.delete', user_key=user.key)
    location_url = url_for('user.detail', user_key=user.key)

    app.get_connection().set_registration(Registration(
        app_grouping.key, user.key, UserPreferences()))
    check_has_groupings(client, url, location_url)
    app.get_connection().delete_registrations(app_grouping.key)

    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    check_has_groupings(client, url, location_url)
    app.get_connection().set_groups(app_grouping.key, ())

    host_key = app_grouping.host_key
    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping, host_key=user.key))
    check_has_groupings(client, url, location_url)
    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping, host_key=host_key))

    check_flash(
        client, client.post(url), url_for('user.users'),
        "success", "User '%s' deleted." % user.ident)
    assert client.post(
        url_for('user.delete', user_key=UserKey(int=0))).status_code == 404
