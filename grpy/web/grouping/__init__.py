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

"""Web access layer for groupings."""

from flask import Blueprint

from . import views


def create_blueprint() -> Blueprint:
    """Create the authentication blueprint."""
    blueprint = Blueprint("grouping", __name__)
    blueprint.add_url_rule(
        "/", "list", views.grouping_list)
    blueprint.add_url_rule(
        "/create", "create", views.grouping_create,
        methods=('GET', 'POST'))
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/", "detail",
        views.grouping_detail, methods=('GET', 'POST'))
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/edit", "update",
        views.grouping_update, methods=('GET', 'POST'))
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/register", "register",
        views.grouping_register, methods=('GET', 'POST'))
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/final", "final",
        views.grouping_final)
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/close", "close",
        views.grouping_close)
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/start", "start",
        views.grouping_start, methods=('GET', 'POST'))
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/remove_groups", "remove_groups",
        views.grouping_remove_groups, methods=('GET', 'POST'))
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/fasten_groups", "fasten_groups",
        views.grouping_fasten_groups, methods=('GET', 'POST'))
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/assign", "assign",
        views.grouping_assign, methods=('GET', 'POST'))
    blueprint.add_url_rule(
        "/<grouping:grouping_key>/delete", "delete",
        views.grouping_delete, methods=('GET', 'POST'))
    return blueprint
