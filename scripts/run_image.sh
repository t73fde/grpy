#!/usr/bin/sh

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

sudo docker run --rm -it \
  --link winauth \
  -p 127.0.0.1:8000:8000 \
  -v "$(pwd)/deploy/docker.cfg":/usr/src/grpy.cfg:ro \
  -v "$(pwd)/db.db":/usr/src/db/grpy.sqlite \
  grpy
