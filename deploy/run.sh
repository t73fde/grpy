#!/bin/sh

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

cd /usr/src
chown -R grpy:grpy grpy
chown grpy:grpy .
chown -R grpy db
cd /usr/src/grpy
cat VERSION.txt
exec su grpy -c 'gunicorn -b 0.0.0.0:8000 -w 3 deploy.wsgi_gunicorn:app'
