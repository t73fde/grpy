#!/bin/bash

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
#    along with grpy. If not, see <https://www.gnu.org/licenses/>.
##

set -e

PY_FILES="grpy grpyweb grpydb scripts wsgi.py"

echo "-- autopep8"
OUTPUT=$(autopep8 --diff --recursive $PY_FILES)
if [[ $OUTPUT ]]; then
  echo "$OUTPUT"
  echo "-- please format source code with 'make fmt'"
  exit 1
fi
echo "-- pydocstyle"
pydocstyle -v -e $PY_FILES
echo "-- Flake8"
flake8 $PY_FILES
echo "-- Dodgy"
dodgy
echo "-- PyLint"
pylint grpy grpydb grpyweb
echo "-- Bandit"
bandit -r -x test .
