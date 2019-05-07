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

"""Common helper functions."""

from typing import cast

from flask import get_flashed_messages, url_for


def check_get(client, url: str, status_code: int = 200):
    """Check GET request and return response."""
    response = client.get(url)
    assert response.status_code == status_code
    return response


def check_get_data(client, url: str) -> str:
    """Retrieve data from URL and return it as a string."""
    return cast(str, check_get(client, url).data.decode('utf-8'))


def check_requests(client, url: str, status_code: int, do_post: bool = True) -> None:
    """Check GET/POST requests for status code."""
    assert client.get(url).status_code == status_code
    if do_post:
        assert client.post(url).status_code == status_code


def check_bad_anon_requests(client, auth, url: str, do_post: bool = True) -> None:
    """Assert that anonymous users cannot access ressource."""
    auth.logout()
    check_requests(client, url, 401, do_post)


def check_redirect(response, location_url: str):
    """Assert that a redirect without flash message will happen."""
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost" + location_url
    assert get_flashed_messages(with_categories=True) == []
    return response


def check_message(client, category: str, message: str) -> None:
    """Assert that flash message will occur."""
    assert get_flashed_messages(with_categories=True) == [(category, message)]
    client.get(url_for('home'))  # Clean flash message


def check_flash(client, response, location_url: str, category: str, message: str):
    """Assert that a redirection with a flash message will occur."""
    assert response.status_code == 302
    assert response.headers['Location'] == "http://localhost" + location_url
    check_message(client, category, message)
    return response
