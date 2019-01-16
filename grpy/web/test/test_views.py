
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

"""Test the web views."""

import datetime
import uuid

from flask import g, session, url_for
from flask.sessions import SecureCookieSessionInterface

from werkzeug.http import parse_cookie

from ... import utils
from ...models import Grouping
from ...repo.logic import set_grouping_new_code


def get_session_data(app, response):
    """Retrieve the session data from a response."""
    cookie = response.headers.get('Set-Cookie')
    if not cookie:
        return {}
    session_str = parse_cookie(cookie)['session']
    session_serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    return session_serializer.loads(session_str)


def test_home_anonymous(client):
    """Test home view as an anonymous user."""
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert ": Home</title>" in data
    assert "Welcome!" in data
    assert url_for('home') in data
    assert url_for('about') in data
    assert url_for('login') in data
    assert url_for('logout') not in data


def insert_simple_grouping(repository):
    """Insert a grouping into the repository."""
    now = utils.now()
    host = repository.get_user_by_username("host")
    return set_grouping_new_code(repository, Grouping(
        None, ".", "Name", host.key, now, now + datetime.timedelta(days=1),
        None, "RD", 17, 7, "Notizie"))


def test_home_host(app, client, auth):
    """Test home view as a host."""
    grouping = insert_simple_grouping(app.get_repository())
    auth.login("host")
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert "host</span>" in data
    assert url_for('grouping_detail', key=grouping.key) in data
    assert grouping.name in data
    assert str(grouping.final_date.minute) in data


def test_home_user(client, auth):
    """Test home view as a participant."""
    auth.login("user")
    response = client.get(url_for('home'))
    data = response.data.decode('utf-8')
    assert "user</span>" in data
    assert " valid grouping link " in data


def test_about_anonymous(client):
    """Test about view as an anonymous user."""
    response = client.get(url_for('about'))
    data = response.data.decode('utf-8')
    assert ": About</title>" in data
    assert url_for('home') in data
    assert url_for('about') in data
    assert url_for('login') in data
    assert url_for('logout') not in data


def test_login(client):
    """Test login view."""
    url = url_for('login')
    assert client.get(url).status_code == 200
    response = client.post(url, data={'username': "host", 'password': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert session['username'] == "host"


def test_login_new_user(app, client):
    """Test login view for new user."""
    response = client.post(
        url_for('login'), data={'username': "new_user", 'password': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert session['username'] == "new_user"
    assert app.get_repository().get_user_by_username("new_user")


def test_invalid_login(client):
    """Test login view for invalid login."""
    url = url_for('login')
    response = client.post(url, data={'username': "xunknown", 'password': "1"})
    assert response.status_code == 200
    assert b"Cannot authenticate user" in response.data
    assert 'username' not in session


def test_double_login(client, auth):
    """A double login makes the last user to be logged in."""
    auth.login("user")
    assert session['username'] == "user"
    assert b"User &#39;user&#39; was logged out." in client.get(url_for('login')).data
    auth.login("host")
    assert session['username'] == "host"


def test_name_change_after_login(app, client, auth):
    """Username is changed after login."""
    auth.login("host")
    repository = app.get_repository()
    user = repository.get_user_by_username("host")
    repository.set_user(user._replace(username="tsoh"))
    client.get("/")
    assert g.user is None


def test_login_with_redirect(app, client):
    """Test login view when redirect after successful login."""
    url = url_for('login', next_url="/ABCDEF/")
    response = client.get(url)
    assert b'<input id="next_url" name="next_url" type="hidden" value="/ABCDEF/">' \
        in response.data

    response = client.post(
        url_for('login'),
        data={'username': "new_user", 'password': "1", 'next_url': "/ABCDEF/"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/ABCDEF/"
    assert session['username'] == "new_user"
    assert app.get_repository().get_user_by_username("new_user")


def test_logout(client, auth):
    """Test login/logout sequence."""
    auth.login("host")
    assert session['username'] == "host"
    response = client.get(url_for('logout'))
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert 'username' not in session


def test_logout_without_login(client):
    """A logout without previous login is ignored."""
    assert 'username' not in session
    response = client.get(url_for('logout'))
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert 'username' not in session


def test_grouping_detail(app, client, auth):
    """Test grouping detail view."""
    grouping = insert_simple_grouping(app.get_repository())
    url = url_for('grouping_detail', key=grouping.key)
    response = client.get(url)
    assert response.status_code == 401

    auth.login("host")
    response = client.get(url)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert grouping.note in data

    auth.login("user")
    response = client.get(url)
    assert response.status_code == 403

    assert client.get(url_for('grouping_detail', key=uuid.uuid4())).status_code == 404


def test_grouping_create(app, client, auth):
    """Test the creation of new groupings."""
    url = url_for('grouping_create')
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
        'strategy': "RD", 'max_group_size': "2", 'member_reserve': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"

    groupings = app.get_repository().iter_groupings(where={"name__eq": "name"})
    assert len(groupings) == 1

    response = client.post(url, data={
        'name': "name", 'begin_date': "1970-01-01 00:00",
        'final_date': "1970-01-01 00:01", 'close_date': "1970-01-01 00:02",
        'strategy': "RD", 'max_group_size': "2", 'member_reserve': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"

    groupings = app.get_repository().iter_groupings(where={"name__eq": "name"})
    assert len(groupings) == 2


def test_grouping_update(app, client, auth):
    """Test the update of an existing grouping."""
    grouping = insert_simple_grouping(app.get_repository())
    url = url_for('grouping_update', key=grouping.key)
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
        'strategy': "RD", 'max_group_size': "2", 'member_reserve': "1"})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"

    groupings = list(app.get_repository().iter_groupings())
    assert len(groupings) == 1
    assert groupings[0].key == grouping.key


def test_shortlink(app, client, auth):
    """Test home view as a host."""
    grouping = insert_simple_grouping(app.get_repository())
    url = url_for('shortlink', code=grouping.code)
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == \
        "http://localhost/login?next_url=%2F{}%2F".format(grouping.code)

    auth.login("host")
    response = client.get(url)
    assert response.status_code == 200
    assert response.data.count(url.encode('utf-8')) == 1

    auth.login("student")
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers['Location'] == \
        "http://localhost" + url_for('grouping_apply', key=grouping.key)


def test_grouping_apply(app, client, auth):
    """Check the grouping registration."""
    grouping = insert_simple_grouping(app.get_repository())
    url = url_for('grouping_apply', key=grouping.key)
    assert client.get(url).status_code == 401
    assert client.post(url).status_code == 401

    auth.login('host')
    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403

    auth.login('student')
    assert client.get(url).status_code == 200
    response = client.get(url)

    response = client.post(url, data={})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "Your registration for '{}' is stored.".format(grouping.name))]

    client.get(url_for('home'))  # Clean flash messages

    response = client.post(url, data={})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert get_session_data(app, response)['_flashes'] == \
        [('info', "Your registration for '{}' is updated.".format(grouping.name))]


def test_grouping_apply_out_of_time(app, client, auth):
    """Check the grouping registration before start date and after final date."""
    grouping = insert_simple_grouping(app.get_repository())
    url = url_for('grouping_apply', key=grouping.key)
    auth.login('student')

    now = utils.now()
    app.get_repository().set_grouping(
        grouping._replace(begin_date=now + datetime.timedelta(seconds=3600)))
    response = client.post(url, data={})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Not within the registration period for '{}'.".format(
            grouping.name))]

    client.get(url_for('home'))  # Clean flash messages

    app.get_repository().set_grouping(
        grouping._replace(
            begin_date=now - datetime.timedelta(seconds=3600),
            final_date=now - datetime.timedelta(seconds=1800)))
    response = client.post(url, data={})
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost/"
    assert get_session_data(app, response)['_flashes'] == \
        [('warning', "Not within the registration period for '{}'.".format(
            grouping.name))]
