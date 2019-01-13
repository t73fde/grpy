

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

"""Some utility functions."""

from functools import wraps
from typing import Any

from flask import abort, g


def login_required(view):
    """Wrap a view to enforce an user who is logged in."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            abort(401)
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
    return model_class._make(map(lambda f: data.get(f, None), model_class._fields))


def update_model(model, form_data):
    """Update a given model with data from a form."""
    fields = set(model._fields)
    return model._replace(**{k: v for k, v in form_data.items() if k in fields})
