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

import dataclasses  # pylint: disable=wrong-import-order
from functools import wraps
from typing import Any, Sequence, Tuple, cast

from flask import (abort, current_app, g, get_flashed_messages, redirect,
                   request, url_for)
from flask_babel import format_datetime
from werkzeug.routing import UUIDConverter

from ..models import GroupingKey


class GroupingKeyConverter(UUIDConverter):
    """An URL converter for GroupingKeys."""

    def to_python(self, value: str) -> GroupingKey:
        """Convert the already parsed URL string into a GroupingKey."""
        return GroupingKey(value)


def login_required(view):
    """Wrap a view to enforce an user who is logged in."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            abort(401)
        return view(*args, **kwargs)
    return wrapped_view


def login_required_redirect(view):
    """Wrap a view to enforce a login of an user."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next_url=request.path))
        return view(*args, **kwargs)
    return wrapped_view


def value_or_404(value: Any) -> Any:
    """If value is None, raise 404."""
    if value is None:
        abort(404)
    return value


def make_model(model_class, form_data, additional_values):
    """Create a new model based on form data."""
    data = dict(form_data)
    data.update(additional_values)
    return model_class(*tuple(map(
        lambda f: data.get(f, None),
        (field.name for field in dataclasses.fields(model_class)))))


def update_model(model, form_data):
    """Update a given model with data from a form."""
    fields = set(field.name for field in dataclasses.fields(model))
    return dataclasses.replace(
        model, **{k: v for k, v in form_data.items() if k in fields})


def datetimeformat(datetime=None, dt_format=None, rebase=True):
    """
    Return a datetime formatted according to format.

    This function is needed, because `flask_babel.format_datetime` formats the
    current datetime, if `datetime` is None.
    """
    if not datetime:
        return datetime
    if dt_format == "iso-short":
        return format_datetime(datetime, "YYYY-MM-dd HH:mm z", rebase)
    return format_datetime(datetime, dt_format, rebase)


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
    }.get(color_description, color_description)


def get_all_messages() -> Sequence[Tuple[str, str]]:
    """Return all messages, not just those from the session."""
    messages = current_app.get_connection().get_messages(delete=False)
    if messages:
        return [(m.category, m.text) for m in messages]
    return cast(Sequence[Tuple[str, str]], get_flashed_messages(with_categories=True))
