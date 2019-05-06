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

"""Test the grouping web views."""

import dataclasses
import datetime
from typing import List, cast

from flask import url_for

from ....core import utils
from ....core.models import (Grouping, GroupingKey, Permissions, Registration,
                             User, UserKey, UserPreferences)
from ....repo.base import Connection
from ...app import GrpyApp
from ...test.common import (check_bad_anon_requests, check_flash, check_get,
                            check_get_data, check_redirect, check_requests)


def check_bad_requests(client, auth, url: str, do_post: bool = True) -> None:
    """Assert that others cannot access resource."""
    auth.login('user')
    check_requests(client, url, 403, do_post)
    auth.login('admin')
    check_requests(client, url, 403, do_post)
    check_bad_anon_requests(client, auth, url, do_post)


def check_bad_host_requests(
        app: GrpyApp, client, auth, url: str, do_post: bool = True) -> None:
    """Assert that other host and other users cannot access resource."""
    app.get_connection().set_user(User(None, "host-0", Permissions.HOST))
    auth.login('host-0')
    check_requests(client, url, 403, do_post)
    check_bad_requests(client, auth, url, do_post)


def test_grouping_create(app: GrpyApp, client, auth) -> None:
    """Test the creation of new groupings."""
    url = url_for('grouping.create')
    check_bad_requests(client, auth, url)

    auth.login('host')
    check_get(client, url)

    response = client.post(url, data={})
    assert response.status_code == 200
    assert response.data.count(b'This field is required') == 5

    check_redirect(
        client.post(url, data={
            'name': "name", 'begin_date': "1970-01-01 00:00",
            'final_date': "1970-01-01 00:01", 'close_date': "1970-01-01 00:02",
            'policy': "RD", 'max_group_size': "2", 'member_reserve': "1"}),
        "/")

    groupings = app.get_connection().iter_groupings(where={"name__eq": "name"})
    assert len(list(groupings)) == 1

    check_redirect(
        client.post(url, data={
            'name': "name", 'begin_date': "1970-01-01 00:00",
            'final_date': "1970-01-01 00:01", 'close_date': "1970-01-01 00:02",
            'policy': "RD", 'max_group_size': "2", 'member_reserve': "1"}),
        "/")

    groupings = app.get_connection().iter_groupings(where={"name__eq": "name"})
    assert len(list(groupings)) == 2


def test_grouping_detail(client, auth, app_grouping: Grouping) -> None:
    """Test grouping detail view."""
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    check_bad_requests(client, auth, url, False)

    auth.login("host")
    data = check_get_data(client, url)
    assert app_grouping.code in data
    assert url_for('shortlink', code=app_grouping.code) in data
    assert app_grouping.note in data

    auth.login("user")
    check_get(client, url, 403)
    check_get(client, url_for('grouping.detail', grouping_key=GroupingKey()), 404)


def test_grouping_detail_no_code(
        app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """When final date is reached, no short link / code should be visible."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping, final_date=utils.now() - datetime.timedelta(seconds=600)))
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login("host")
    data = check_get_data(client, url)
    assert app_grouping.code not in data
    assert url_for('shortlink', code=app_grouping.code) not in data


def add_user_registrations(app: GrpyApp, grouping_key: GroupingKey) -> List[User]:
    """Add some users and register them for the grouping."""
    users = []
    for i in range(12):
        user = app.get_connection().set_user(User(None, "user%d" % i))
        assert user.key is not None
        app.get_connection().set_registration(Registration(
            grouping_key, user.key, UserPreferences()))
        users.append(user)
    return users


def test_grouping_detail_remove(
        app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Test removal of registrations."""
    assert app_grouping.key is not None
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    users = add_user_registrations(app, app_grouping.key)
    auth.login("host")
    data = check_get_data(client, url)
    for user in users:
        assert user.ident in data
        assert str(user.key) in data

    count = 0
    while users:
        to_delete = users[:count]
        users = users[count:]
        count += 1
        check_flash(
            client,
            client.post(url, data={
                'u': [str(u.key) for u in to_delete],
            }),
            url, "info", "{} registered users removed.".format(len(to_delete)))


def test_grouping_detail_remove_grouped(
        app, client, auth, app_grouping: Grouping) -> None:
    """Registered users are not shown when groups were formed."""
    assert app_grouping.key is not None
    users = add_user_registrations(app, app_grouping.key)
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000)))
    users_as_group = frozenset(user.key for user in users)
    app.get_connection().set_groups(app_grouping.key, (users_as_group,))
    auth.login("host")
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    assert b"registered users" not in check_get(client, url).data.lower()


def test_grouping_detail_remove_illegal(client, auth, app_grouping: Grouping) -> None:
    """If illegal UUIDs are sent, nothing happens."""
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login("host")
    for data in ("1,2,3", [str(app_grouping.key)]):
        check_flash(
            client,
            client.post(url, data={'u': data}),
            url, "info", "0 registered users removed.")


def test_grouping_detail_fasten(
        app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """
    Test visibility of button 'Fasten groups'.

    A group assignment can be fastened, if state of grouping is
    `GroupingState.GROUPED`.
    """
    assert app_grouping.key is not None
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000)))
    assert app_grouping.key is not None
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login("host")
    response = client.get(url)
    assert b"<h1>Groups</h1>" not in response.data
    assert b"Fasten" not in response.data
    assert b"Remove Groups" not in response.data

    users = add_user_registrations(app, app_grouping.key)
    response = client.get(url)
    assert b"<h1>Groups</h1>" not in response.data
    assert b"Fasten" not in response.data
    assert b"Remove Groups" not in response.data

    users_as_group = frozenset(cast(UserKey, user.key) for user in users)
    app.get_connection().set_groups(app_grouping.key, (users_as_group,))
    data = check_get_data(client, url)
    assert "<h1>Groups</h1>" in data
    assert "Fasten" in data
    assert url_for('grouping.fasten_groups', grouping_key=app_grouping.key) in data
    assert "Remove Groups" in data

    app.get_connection().delete_registrations(app_grouping.key)
    data = check_get_data(client, url)
    assert "<h1>Groups</h1>" in data
    assert "Fasten" not in data
    assert "Remove Groups" not in data


def test_grouping_update(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Test the update of an existing grouping."""
    url = url_for('grouping.update', grouping_key=app_grouping.key)
    check_bad_host_requests(app, client, auth, url)

    auth.login('host')
    check_get(client, url)
    response = client.post(url, data={})
    assert response.status_code == 200
    assert response.data.count(b'This field is required') == 5

    check_redirect(
        client.post(url, data={
            'name': "very new name", 'begin_date': "1970-01-01 00:00",
            'final_date': "1970-01-01 00:01", 'close_date': "1970-01-01 00:02",
            'policy': "RD", 'max_group_size': "2", 'member_reserve': "1"}),
        url_for('.detail', grouping_key=app_grouping.key))

    groupings = list(app.get_connection().iter_groupings())
    assert len(groupings) == 1
    assert groupings[0].key == app_grouping.key

    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000),
        close_date=None))
    assert app_grouping.key is not None
    user = app.get_connection().get_user_by_ident("user")
    assert user is not None
    assert user.key is not None
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))

    check_flash(
        client, client.get(url), "/", "warning",
        "Update of grouping not allowed.")


def test_grouping_register(client, auth, app_grouping: Grouping) -> None:
    """Check the grouping registration."""
    url = url_for('grouping.register', grouping_key=app_grouping.key)
    check_bad_anon_requests(client, auth, url)

    auth.login('host')
    check_get(client, url, 403)
    assert client.post(url).status_code == 403

    auth.login('student')
    check_get(client, url)
    check_flash(
        client,
        client.post(url, data={'submit_register': "submit_register"}),
        "/", "info", "Registration for '{}' is stored.".format(app_grouping.name))

    check_flash(
        client,
        client.post(url, data={'submit_register': "submit_register"}),
        "/", "info", "Registration for '{}' is updated.".format(app_grouping.name))

    data = check_get_data(client, url_for('home'))
    assert "Registered Groupings" in data
    assert app_grouping.name in data
    assert "Welcome!" not in data


def test_grouping_register_out_of_time(
        app, client, auth, app_grouping: Grouping) -> None:
    """Check the grouping registration before start date and after final date."""
    url = url_for('grouping.register', grouping_key=app_grouping.key)
    auth.login('student')

    now = utils.now()
    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping, begin_date=now + datetime.timedelta(seconds=3600)))
    check_flash(
        client, client.post(url, data={}),
        "/", "warning", "Grouping '{}' is not available.".format(app_grouping.name))

    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        begin_date=now - datetime.timedelta(seconds=3600),
        final_date=now - datetime.timedelta(seconds=1800)))
    check_flash(
        client, client.post(url, data={}),
        "/", "warning", "Grouping '{}' is not available.".format(app_grouping.name))


def test_grouping_start(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Test group building view."""
    assert app_grouping.key is not None
    url = url_for('grouping.start', grouping_key=app_grouping.key)
    check_bad_host_requests(app, client, auth, url)

    location_url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login('host')
    check_flash(
        client, client.get(url), location_url, "warning", "Grouping is not final.")

    new_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        begin_date=utils.now() - datetime.timedelta(days=7),
        final_date=utils.now() - datetime.timedelta(seconds=1)))
    assert new_grouping.key is not None
    check_flash(
        client, client.get(url), location_url, "warning",
        "No registrations for '{}' found.".format(new_grouping.name))

    user = app.get_connection().get_user_by_ident("user")
    assert user is not None
    assert user.key is not None
    app.get_connection().set_registration(
        Registration(new_grouping.key, user.key, UserPreferences()))
    assert "Start" in check_get_data(client, url)

    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    check_flash(
        client, client.get(url), location_url, "warning", "Grouping is not final.")


def test_grouping_detail_no_group(client, auth, app_grouping: Grouping) -> None:
    """A fresh grouping has no calculated groups."""
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login("host")
    data = check_get_data(client, url)
    assert "Groups" not in data
    assert "Member</td>" not in data


def create_registered_users(
        connection: Connection, grouping_key: GroupingKey) -> List[User]:
    """Create a bunch of users and register them for the grouping."""
    users = []
    for i in range(20):
        user = connection.set_user(User(None, "user_%d" % i))
        assert user.key is not None
        connection.set_registration(
            Registration(grouping_key, user.key, UserPreferences()))
        users.append(user)
    return users


def start_grouping(
        client, auth, connection: Connection, app_grouping: Grouping):
    """Build the group."""
    url = url_for('grouping.start', grouping_key=app_grouping.key)
    connection.set_grouping(dataclasses.replace(
        app_grouping,
        begin_date=utils.now() - datetime.timedelta(days=7),
        final_date=utils.now() - datetime.timedelta(seconds=1),
        max_group_size=6, member_reserve=5))
    auth.login('host')
    response = client.post(url)
    return response


def test_grouping_build(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Test the group building process."""
    assert app_grouping.key is not None
    users = create_registered_users(app.get_connection(), app_grouping.key)

    detail_url = url_for('grouping.detail', grouping_key=app_grouping.key)
    check_redirect(
        start_grouping(client, auth, app.get_connection(), app_grouping),
        detail_url)

    data = check_get_data(client, detail_url)
    assert "Groups" in data
    assert "Member</td>" in data
    for user in users:
        assert user.ident in data

    home_url = url_for('home')
    for user in users:
        auth.login(user.ident)
        data = check_get_data(client, home_url)
        assert data.count(user.ident) > 1
        assert data.count(app_grouping.name) == 1


def test_grouping_delete_after_build(
        app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """User is deleted after groups are formed, it must be removed from group."""
    assert app_grouping.key is not None
    users = create_registered_users(app.get_connection(), app_grouping.key)
    check_redirect(
        start_grouping(client, auth, app.get_connection(), app_grouping),
        url_for('grouping.detail', grouping_key=app_grouping.key))

    # Now deregister one user
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    check_flash(
        client,
        client.post(url, data={'u': [users[0].key]}),
        url_for('grouping.detail', grouping_key=app_grouping.key),
        "info", "1 registered users removed.")

    # This user must not be in the freshly formed group
    other_users = {user.key for user in users if user != users[0]}
    for group in app.get_connection().get_groups(app_grouping.key):
        for member in group:
            assert member != users[0].key
            assert member in other_users
            other_users.remove(member)
    assert users[0].key not in other_users
    assert other_users == set()


def test_remove_groups(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Groups can be removed after building them."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000)))
    assert app_grouping.key is not None
    url = url_for('grouping.remove_groups', grouping_key=app_grouping.key)
    check_bad_host_requests(app, client, auth, url)

    location_url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login('host')
    check_flash(
        client, client.get(url), location_url, "info", "No groups to remove.")

    user = app.get_connection().get_user_by_ident("user")
    assert user is not None
    assert user.key is not None
    app.get_connection().set_registration(Registration(
        app_grouping.key, user.key, UserPreferences()))
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    check_get(client, url)
    check_redirect(client.post(url, data={}), location_url)
    check_flash(
        client,
        client.post(url, data={'submit_remove': "submit_remove"}),
        location_url, "info", "Groups removed.")
    assert app.get_connection().get_groups(app_grouping.key) == ()


def test_grouping_final(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Final date can be set."""
    url = url_for('grouping.final', grouping_key=app_grouping.key)
    check_bad_host_requests(app, client, auth, url, False)

    auth.login('host')
    detail_url = url_for('grouping.detail', grouping_key=app_grouping.key)
    assert url in check_get_data(client, detail_url)
    check_flash(
        client, client.get(url), detail_url, "info", "Final date is now set.")

    yet = utils.now()
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=yet - datetime.timedelta(seconds=600)))
    user = app.get_connection().set_user(User(None, "uSer-42"))
    assert app_grouping.key
    assert user.key
    app.get_connection().set_registration(Registration(
        app_grouping.key, user.key, UserPreferences()))
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    assert url not in check_get_data(client, detail_url)
    check_flash(
        client, client.get(url), detail_url,
        "warning", "Final date cannot be set now.")

    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        begin_date=yet + datetime.timedelta(seconds=3600),
        final_date=yet + datetime.timedelta(seconds=7200)))
    assert url not in check_get_data(client, detail_url)
    check_flash(
        client, client.get(url), detail_url,
        "warning", "Final date cannot be set now.")


def test_grouping_close(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Close date can be set easily."""
    assert app_grouping.key is not None
    url = url_for('grouping.close', grouping_key=app_grouping.key)
    check_bad_host_requests(app, client, auth, url, False)

    auth.login('host')
    detail_url = url_for('grouping.detail', grouping_key=app_grouping.key)
    assert url not in check_get_data(client, detail_url)
    check_flash(
        client, client.get(url), detail_url,
        "warning", "Close date cannot be set now.")

    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000)))
    assert app_grouping.key is not None

    check_flash(
        client, client.get(url), detail_url, "info", "Close date is now set.")
    grouping = app.get_connection().get_grouping(app_grouping.key)
    assert grouping is not None
    assert grouping.close_date is not None

    check_flash(
        client, client.get(url), detail_url, "info", "Close date removed.")
    grouping = app.get_connection().get_grouping(app_grouping.key)
    assert grouping is not None
    assert grouping.close_date is None


def test_fasten_groups(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """Groups can be fastened after building them."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000)))
    url = url_for('grouping.fasten_groups', grouping_key=app_grouping.key)
    check_bad_host_requests(app, client, auth, url)

    location_url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login('host')
    check_flash(
        client, client.get(url), location_url, "warning",
        "Grouping not performed recently.")

    user = app.get_connection().set_user(User(None, "uSer-42"))
    assert app_grouping.key
    assert user.key
    app.get_connection().set_registration(Registration(
        app_grouping.key, user.key, UserPreferences()))
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    assert check_get_data(client, url).count(user.ident) == 1

    check_redirect(client.post(url, data={}), location_url)

    check_flash(
        client,
        client.post(url, data={'submit_fasten': "submit_fasten"}),
        location_url, "info", "Groups fastened.")
    assert app.get_connection().get_groups(app_grouping.key) == (frozenset([user.key]),)
    assert app.get_connection().count_registrations_by_grouping(app_grouping.key) == 0

    check_flash(
        client, client.get(url), location_url, "warning",
        "Grouping not performed recently.")


def test_delete_grouping_auth(
        app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """A grouping cannot be deleted."""
    url = url_for('grouping.delete', grouping_key=app_grouping.key)
    check_bad_host_requests(app, client, auth, url)

    location_url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login('host')
    check_flash(
        client, client.get(url), location_url,
        "warning", "Grouping cannot be deleted.")


def test_delete_grouping(app: GrpyApp, client, auth, app_grouping: Grouping) -> None:
    """A grouping can be deleted."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.begin_date + datetime.timedelta(seconds=5),
        close_date=app_grouping.begin_date + datetime.timedelta(seconds=9)))
    assert app_grouping.key is not None
    user = app.get_connection().set_user(User(None, "user_del"))
    assert user.key is not None
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    url = url_for('grouping.delete', grouping_key=app_grouping.key)

    auth.login('host')
    check_get(client, url)
    check_redirect(
        client.post(url, data={'submit_cancel': "submit_cancel"}),
        url_for('grouping.detail', grouping_key=app_grouping.key))

    check_flash(
        client,
        client.post(url, data={'submit_delete': "submit_delete"}),
        "/", "info", "Grouping '{}' deleted.".format(app_grouping.name))
    assert app.get_connection().get_grouping(app_grouping.key) is None

    check_requests(client, url, 404, False)
