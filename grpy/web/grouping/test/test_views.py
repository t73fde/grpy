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
from typing import Any, Dict, List, cast

from flask import url_for
from flask.sessions import SecureCookieSessionInterface
from werkzeug.http import parse_cookie

from .... import utils
from ....models import (Grouping, GroupingKey, Registration, User,
                        UserPreferences)
from ....repo.base import Connection


def get_session_data(app, response) -> Dict[str, Any]:
    """Retrieve the session data from a response."""
    cookie = response.headers.get('Set-Cookie')
    if not cookie:
        return {}
    session_str = parse_cookie(cookie)['session']
    session_serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    return cast(Dict[str, Any], session_serializer.loads(session_str))


def test_grouping_create(app, client, auth) -> None:
    """Test the creation of new groupings."""
    url = url_for('grouping.create')
    assert client.get(url).status_code == 401
    assert client.post(url).status_code == 401

    auth.login('user')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    auth.login('host')
    assert client.get(url).status_code == 200

    response = client.post(url, data={})
    assert response.status_code == 200
    assert response.data.count(b'This field is required') == 5

    response = client.post(url, data={
        'name': "name", 'begin_date': "1970-01-01 00:00",
        'final_date': "1970-01-01 00:01", 'close_date': "1970-01-01 00:02",
        'policy': "RD", 'max_group_size': "2", 'member_reserve': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"

    groupings = app.get_connection().iter_groupings(where={"name__eq": "name"})
    assert len(list(groupings)) == 1

    response = client.post(url, data={
        'name': "name", 'begin_date': "1970-01-01 00:00",
        'final_date': "1970-01-01 00:01", 'close_date': "1970-01-01 00:02",
        'policy': "RD", 'max_group_size': "2", 'member_reserve': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"

    groupings = app.get_connection().iter_groupings(where={"name__eq": "name"})
    assert len(list(groupings)) == 2


def test_grouping_detail(client, auth, app_grouping: Grouping) -> None:
    """Test grouping detail view."""
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    response = client.get(url)
    assert response.status_code == 401

    auth.login("host")
    response = client.get(url)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert app_grouping.code in data
    assert url_for('shortlink', code=app_grouping.code) in data
    assert app_grouping.note in data

    auth.login("user")
    response = client.get(url)
    assert response.status_code == 403

    assert client.get(
        url_for('grouping.detail', grouping_key=GroupingKey())).status_code == 404


def test_grouping_detail_no_code(app, client, auth, app_grouping: Grouping) -> None:
    """When final date is reached, no short link / code should be visible."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping, final_date=utils.now() - datetime.timedelta(seconds=600)))
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login("host")
    response = client.get(url)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert app_grouping.code not in data
    assert url_for('shortlink', code=app_grouping.code) not in data


def add_user_registrations(app, grouping_key: GroupingKey) -> List[User]:
    """Add some users and register them for the grouping."""
    users = []
    for i in range(12):
        user = app.get_connection().set_user(User(None, "user%d" % i))
        app.get_connection().set_registration(Registration(
            grouping_key, user.key, UserPreferences()))
        users.append(user)
    return users


def test_grouping_detail_remove(app, client, auth, app_grouping: Grouping) -> None:
    """Test removal of registrations."""
    assert app_grouping.key is not None
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    users = add_user_registrations(app, app_grouping.key)
    auth.login("host")
    response = client.get(url)
    data = response.data.decode('utf-8')
    for user in users:
        assert user.ident in data
        assert str(user.key) in data

    count = 0
    while users:
        to_delete = users[:count]
        users = users[count:]
        count += 1
        response = client.post(url, data={
            'u': [str(u.key) for u in to_delete],
        })
        assert response.status_code == 302
        assert response.headers['Location'] == "http://localhost" + url
        assert get_session_data(app, response)['_flashes'] == \
            [('info', "{} registered users removed.".format(len(to_delete)))]
        client.get(url_for('home'))  # Clean flash message


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
    response = client.get(url)
    assert response.status_code == 200
    assert b"registered users" not in response.data.lower()


def test_grouping_detail_remove_illegal(
        app, client, auth, app_grouping: Grouping) -> None:
    """If illegal UUIDs are sent, nothing happens."""
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    auth.login("host")
    for data in ("1,2,3", [str(app_grouping.key)]):
        response = client.post(url, data={'u': data})
        assert response.status_code == 302
        assert response.headers['Location'] == "http://localhost" + url
        assert get_session_data(app, response)['_flashes'] == \
            [('info', "0 registered users removed.")]
        client.get(url_for('home'))  # Clean flash message


def test_grouping_detail_fasten(app, client, auth, app_grouping: Grouping) -> None:
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

    users_as_group = frozenset(user.key for user in users)
    app.get_connection().set_groups(app_grouping.key, (users_as_group,))
    response = client.get(url)
    assert b"<h1>Groups</h1>" in response.data
    assert b"Fasten" in response.data
    fasten_url = url_for('grouping.fasten_groups', grouping_key=app_grouping.key)
    assert fasten_url.encode('utf-8') in response.data
    assert b"Remove Groups" in response.data

    app.get_connection().delete_registrations(app_grouping.key)
    response = client.get(url)
    assert b"<h1>Groups</h1>" in response.data
    assert b"Fasten" not in response.data
    assert b"Remove Groups" not in response.data


def test_grouping_update(app, client, auth, app_grouping: Grouping) -> None:
    """Test the update of an existing grouping."""
    url = url_for('grouping.update', grouping_key=app_grouping.key)
    assert client.get(url).status_code == 401
    assert client.post(url).status_code == 401

    auth.login('user')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    auth.login('host-0')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    auth.login('host')
    assert client.get(url).status_code == 200

    response = client.post(url, data={})
    assert response.status_code == 200
    assert response.data.count(b'This field is required') == 5

    response = client.post(url, data={
        'name': "very new name", 'begin_date': "1970-01-01 00:00",
        'final_date': "1970-01-01 00:01", 'close_date': "1970-01-01 00:02",
        'policy': "RD", 'max_group_size': "2", 'member_reserve': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    client.get(url_for('home'))  # Clean flash messages

    groupings = list(app.get_connection().iter_groupings())
    assert len(groupings) == 1
    assert groupings[0].key == app_grouping.key

    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000),
        close_date=None))
    assert app_grouping.key is not None
    user = app.get_connection().get_user_by_ident("user")
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    assert client.get(url).status_code == 302
    assert response.headers['Location'] == "http://localhost/"


def test_grouping_register(app, client, auth, app_grouping: Grouping) -> None:
    """Check the grouping registration."""
    url = url_for('grouping.register', grouping_key=app_grouping.key)
    assert client.get(url).status_code == 401
    assert client.post(url).status_code == 401

    auth.login('host')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    auth.login('student')
    assert client.get(url).status_code == 200
    response = client.get(url)

    response = client.post(url, data={'submit_register': "submit_register"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "Registration for '{}' is stored.".format(app_grouping.name))]

    client.get(url_for('home'))  # Clean flash messages

    response = client.post(url, data={'submit_register': "submit_register"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "Registration for '{}' is updated.".format(app_grouping.name))]

    response = client.get(url_for('home'))
    assert response.status_code == 200
    data = response.data.decode('utf-8')
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
    response = client.post(url, data={})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Grouping '{}' is not available.".format(
            app_grouping.name))]

    client.get(url_for('home'))  # Clean flash messages

    app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        begin_date=now - datetime.timedelta(seconds=3600),
        final_date=now - datetime.timedelta(seconds=1800)))
    response = client.post(url, data={})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Grouping '{}' is not available.".format(
            app_grouping.name))]


def test_grouping_start(app, client, auth, app_grouping: Grouping) -> None:
    """Test group building view."""
    url = url_for('grouping.start', grouping_key=app_grouping.key)
    assert client.get(url).status_code == 401
    assert client.post(url).status_code == 401

    auth.login('user')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    auth.login('host-0')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    location_url = "http://localhost" + url_for(
        'grouping.detail', grouping_key=app_grouping.key)
    auth.login('host')
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Grouping is not final.")]
    client.get(url_for('home'))  # Clear flashes

    new_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        begin_date=utils.now() - datetime.timedelta(days=7),
        final_date=utils.now() - datetime.timedelta(seconds=1)))
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "No registrations for '{}' found.".format(new_grouping.name))]
    client.get(url_for('home'))  # Clear flashes

    user = app.get_connection().get_user_by_ident("user")
    app.get_connection().set_registration(
        Registration(new_grouping.key, user.key, UserPreferences()))

    response = client.get(url)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert "Start" in data

    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    response = client.get(url)
    assert response.status_code == 302
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Grouping is not final.")]
    client.get(url_for('home'))  # Clear flashes


def test_grouping_detail_no_group(client, auth, app_grouping: Grouping) -> None:
    """A fresh grouping has no calculated groups."""
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    response = client.get(url)
    auth.login("host")
    response = client.get(url)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
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


def test_grouping_build(app, client, auth, app_grouping: Grouping) -> None:
    """Test the group building process."""
    assert app_grouping.key is not None
    users = create_registered_users(app.get_connection(), app_grouping.key)

    response = start_grouping(client, auth, app.get_connection(), app_grouping)
    assert response.status_code == 302
    detail_url = url_for('grouping.detail', grouping_key=app_grouping.key)
    assert response.headers['Location'] == "http://localhost" + detail_url
    response = client.get(detail_url)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert "Groups" in data
    assert "Member</td>" in data
    for user in users:
        assert user.ident in data

    home_url = url_for('home')
    for user in users:
        auth.login(user.ident)
        response = client.get(home_url)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert data.count(user.ident) > 1
        assert data.count(app_grouping.name) == 1


def test_grouping_delete_after_build(app, client, auth, app_grouping: Grouping) -> None:
    """User is deleted after groups are formed, it must be removed from group."""
    assert app_grouping.key is not None
    users = create_registered_users(app.get_connection(), app_grouping.key)
    response = start_grouping(client, auth, app.get_connection(), app_grouping)
    assert response.status_code == 302

    # Now deregister one user
    url = url_for('grouping.detail', grouping_key=app_grouping.key)
    response = client.post(url, data={
        'u': [users[0].key],
    })
    assert response.status_code == 302

    # This user must not be in the freshly formed group
    other_users = {user.key for user in users if user != users[0]}
    for group in app.get_connection().get_groups(app_grouping.key):
        for member in group:
            assert member != users[0].key
            assert member in other_users
            other_users.remove(member)
    assert users[0].key not in other_users
    assert other_users == set()


def test_remove_groups(app, client, auth, app_grouping: Grouping) -> None:
    """Groups can be removed after building them."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000)))
    assert app_grouping.key is not None
    url = url_for('grouping.remove_groups', grouping_key=app_grouping.key)
    assert client.get(url).status_code == 401
    assert client.post(url).status_code == 401

    auth.login('user')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    auth.login('host-0')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    location_url = "http://localhost" + url_for(
        'grouping.detail', grouping_key=app_grouping.key)
    auth.login('host')
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "No groups to remove.")]
    client.get(url_for('home'))  # Clear flashes

    user = app.get_connection().get_user_by_ident("user")
    app.get_connection().set_registration(Registration(
        app_grouping.key, user.key, UserPreferences()))
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    response = client.get(url)
    assert response.status_code == 200

    response = client.post(url, data={})
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert '_flashes' not in get_session_data(app, response)

    response = client.post(url, data={'submit_remove': "submit_remove"})
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "Groups removed.")]
    client.get(url_for('home'))  # Clear flashes
    assert app.get_connection().get_groups(app_grouping.key) == ()


def test_grouping_close(app, client, auth, app_grouping: Grouping) -> None:
    """Close date can be set easily."""
    url = url_for('grouping.close', grouping_key=app_grouping.key)
    assert client.get(url).status_code == 401
    auth.login('user')
    assert client.get(url).status_code == 403
    auth.login('host-0')
    assert client.get(url).status_code == 403

    location_url = "http://localhost" + url_for(
        'grouping.detail', grouping_key=app_grouping.key)
    auth.login('host')
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Please wait until final date is reached.")]
    client.get(url_for('home'))  # Clear flashes

    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000)))

    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "Close date is now set.")]
    client.get(url_for('home'))  # Clear flashes
    assert app.get_connection().get_grouping(app_grouping.key).close_date is not None

    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "Close date removed.")]
    client.get(url_for('home'))  # Clear flashes
    assert app.get_connection().get_grouping(app_grouping.key).close_date is None


def test_fasten_groups(app, client, auth, app_grouping: Grouping) -> None:
    """Groups can be fastened after building them."""
    app_grouping = app.get_connection().set_grouping(dataclasses.replace(
        app_grouping,
        final_date=app_grouping.final_date - datetime.timedelta(seconds=90000)))
    url = url_for('grouping.fasten_groups', grouping_key=app_grouping.key)
    assert client.get(url).status_code == 401
    assert client.post(url).status_code == 401

    auth.login('user')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    auth.login('host-0')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    location_url = "http://localhost" + url_for(
        'grouping.detail', grouping_key=app_grouping.key)
    auth.login('host')
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Grouping not performed recently.")]
    client.get(url_for('home'))  # Clear flashes

    user = app.get_connection().set_user(User(None, "uSer-42"))
    assert app_grouping.key
    assert user.key
    app.get_connection().set_registration(Registration(
        app_grouping.key, user.key, UserPreferences()))
    app.get_connection().set_groups(app_grouping.key, (frozenset([user.key]),))
    response = client.get(url)
    assert response.status_code == 200
    assert response.data.count(user.ident.encode('utf-8')) == 1

    response = client.post(url, data={})
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert '_flashes' not in get_session_data(app, response)

    response = client.post(url, data={'submit_fasten': "submit_fasten"})
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "Groups fastened.")]
    client.get(url_for('home'))  # Clear flashes
    assert app.get_connection().get_groups(app_grouping.key) == (frozenset([user.key]),)
    assert app.get_connection().count_registrations_by_grouping(app_grouping.key) == 0

    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == location_url
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Grouping not performed recently.")]
    client.get(url_for('home'))  # Clear flashes