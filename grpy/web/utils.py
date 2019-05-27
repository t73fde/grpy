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

"""Some utility functions for the web application."""

import dataclasses
import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypeVar, cast

import pytz
from flask import (abort, current_app, g, get_flashed_messages, redirect,
                   request, session, url_for)
from flask_babel import format_datetime
from werkzeug.routing import UUIDConverter

from ..core.models import GroupingKey, Model, UserKey


class GroupingKeyConverter(UUIDConverter):
    """An URL converter for GroupingKeys."""

    def to_python(self, value: str) -> GroupingKey:
        """Convert the already parsed URL string into a GroupingKey."""
        return GroupingKey(value)


class UserKeyConverter(UUIDConverter):
    """An URL converter for UserKeys."""

    def to_python(self, value: str) -> UserKey:
        """Convert the already parsed URL string into a UserKey."""
        return UserKey(value)


def to_bool(value: Any) -> bool:
    """
    Convert value to boolean value.

    This function is used mostly for configuration values, that should be
    interpreted as a boolean value. Since configuration values could be
    specified via environment variables that are string, some kind of
    conversion is needed.

    All values except string values are converted via `bool` function.
    A string value of `""`, `"0"` is converted to `False`, also any string
    value that starts with `"F"` or `"f"`. All other values are converted to
    `True`.
    """
    if not isinstance(value, str):
        return bool(value)
    if value:
        if value == "0" or value[0] == "F" or value[0] == "f":
            return False
        return True
    return False


def login_required(view):
    """Wrap a view to enforce an user who is logged in."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None or not g.user.is_active:
            abort(401)
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    """Wrap a view to enforce an user who is logged in as an administrator."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None or not g.user.is_active:
            abort(401)
        if not g.user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped_view


def redirect_to_login() -> Any:
    """Return a redirect to login view."""
    return redirect(url_for('auth.login', next_url=request.script_root + request.path))


def login_required_redirect(view):
    """Wrap a view to enforce a login of an user."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect_to_login()
        if not g.user.is_active:
            abort(401)
        return view(*args, **kwargs)
    return wrapped_view


TYPE = TypeVar('TYPE')


def value_or_404(value: Optional[TYPE]) -> TYPE:
    """If value is None, raise 404."""
    if value is None:
        abort(404)
    return value


def make_model(model_class, form_data: Dict, additional_values: Dict) -> Model:
    """Create a new model based on form data."""
    data = dict(form_data)
    data.update(additional_values)
    fields = dataclasses.fields(model_class)
    default_dict = {
        f.name: f.default for f in fields if f.default != dataclasses.MISSING}
    return cast(Model, model_class(*tuple(map(
        lambda name: data.get(name, default_dict.get(name, None)),
        (field.name for field in fields)))))


def update_model(model: Model, form_data):
    """Update a given model with data from a form."""
    fields = set(field.name for field in dataclasses.fields(model))
    return dataclasses.replace(
        model, **{k: v for k, v in form_data.items() if k in fields})


def local2utc(dt_value: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
    """Convert a local date time value into utc time zone."""
    if dt_value is None:
        return None
    local_value = current_app.default_tz.localize(dt_value)
    return cast(datetime.datetime, local_value.astimezone(pytz.UTC))


def utc2local(dt_value: datetime.datetime) -> datetime.datetime:
    """Convert a date time of utc time zone into local time zone."""
    return dt_value.astimezone(current_app.default_tz)


def datetimeformat(
        dt_value: Optional[datetime.datetime] = None,
        dt_format: Optional[str] = None,
        rebase: bool = True) -> Optional[str]:
    """
    Return a datetime formatted according to format.

    This function is needed, because `flask_babel.format_datetime` formats the
    current datetime, if `datetime` is None.
    """
    if not dt_value:
        return None
    dt_value = utc2local(dt_value)
    if dt_format == "iso-short":
        return cast(str, format_datetime(dt_value, "YYYY-MM-dd HH:mm", rebase=False))
    return cast(str, format_datetime(dt_value, dt_format, rebase))


def colormap(color_description: str, prefix: str = "w3-") -> str:
    """Map a color description to a W3.CSS color."""
    return prefix + {
        'navbar': "indigo",
        'primary': "indigo",
        'secondary': "blue-gray",
        'success': "teal",
        'critical': "red",
        'danger': "red",
        'error': "red",
        'warning': "yellow",
        'info': "cyan",
        'message': "cyan",
        'heading': "light-gray",
        'form': "blue",
    }.get(color_description, color_description)


def get_all_messages() -> Sequence[Tuple[str, str]]:
    """Return all messages, not just those from the session."""
    get_messages: List[Tuple[str, str]] = [
        (m.category, m.text)
        for m in current_app.get_connection().get_messages()]
    if get_messages:
        return get_messages
    post_messages: List[Tuple[str, str]] = session.get('connection_messages', [])
    if post_messages:
        del session['connection_messages']
        return post_messages
    return cast(Sequence[Tuple[str, str]], get_flashed_messages(with_categories=True))


def truncate(length: int, value: str) -> str:
    """Return string value with a maximal length."""
    if len(value) <= length:
        return value
    if length < 0:
        return ""
    return value[0:max(length, 3) - 3] + "..."
