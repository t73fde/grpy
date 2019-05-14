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

FROM hshnwinps/pydev as builder
WORKDIR /home
COPY . /home
RUN python setup.py --quiet sdist \
 && mv dist/* dist/grpy.tar.gz

FROM python:3.7-alpine
COPY --from=builder /home/dist/grpy.tar.gz /home/VERSION.txt /
RUN set -ex \
 && apk update \
 && pip install -U pip \
 && pip install /grpy.tar.gz \
 && cd /usr/src \
 && tar xfz /grpy.tar.gz \
 && rm /grpy.tar.gz /VERSION.txt \
 && mv grpy-* grpy \
 && rm -rf grpy/grpy \
 && addgroup grpy \
 && adduser -D -H -G grpy grpy \
 && mkdir db \
 && rm -rf /root/.cache /root/.local /root/.virtualenvs \
 && rm -rf /var/cache/apk/*

# USER nobody
WORKDIR /
ENV GRPY_CONFIG=/usr/src/grpy.cfg
CMD ["/usr/src/grpy/deploy/run.sh"]
