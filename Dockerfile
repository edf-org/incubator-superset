#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
FROM python:3.6

RUN useradd --user-group --create-home --no-log-init --shell /bin/bash superset

ARG SUPERSET_VERSION=0.32.0rc2

# Configure environment
ENV GUNICORN_BIND=0.0.0.0:8088 \
    GUNICORN_LIMIT_REQUEST_FIELD_SIZE=0 \
    GUNICORN_LIMIT_REQUEST_LINE=0 \
    GUNICORN_TIMEOUT=60 \
    GUNICORN_WORKERS=2 \
	LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONPATH=/etc/superset:/home/superset:$PYTHONPATH \
    SUPERSET_REPO=apache/incubator-superset \
    SUPERSET_VERSION=${SUPERSET_VERSION} \
    SUPERSET_HOME=/home/superset/superset

RUN apt-get update -y

# Install dependencies to fix `curl https support error` and `elaying package configuration warning`
RUN apt-get install -y apt-transport-https apt-utils

# Install superset dependencies
# https://superset.incubator.apache.org/installation.html#os-dependencies
RUN apt-get install -y build-essential libssl-dev \
    libffi-dev python3-dev libsasl2-dev libldap2-dev libxi-dev

# Install extra useful tool for development
RUN apt-get install -y vim less postgresql-client redis-tools

# Install nodejs for custom build
# https://superset.incubator.apache.org/installation.html#making-your-own-build
# https://nodejs.org/en/download/package-manager/
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && apt-get install -y nodejs

WORKDIR /home/superset

COPY requirements.txt .
COPY requirements-dev.txt .

RUN pip install --upgrade setuptools pip \
    && pip install -r requirements.txt -r requirements-dev.txt \
    && rm -rf /root/.cache/pip

COPY --chown=superset:superset superset superset

ENV PATH=/home/superset/superset/bin:$PATH \
    PYTHONPATH=/home/superset/superset/:$PYTHONPATH

USER superset

RUN cd superset/assets \
    && npm ci \
    && npm run sync-backend \
    && npm run build \
    && rm -rf node_modules

COPY contrib/docker/docker-init.sh .

# RUN ./docker-init.sh

COPY contrib/docker/docker-entrypoint.sh /entrypoint.sh

ADD superset_config.py /home/superset/superset_config.py
ADD superset_config.py /etc/superset/superset_config.py


# RUN sed -i 's/<head>/<head><link rel="icon" href="\/assets\/img\/favicon.ico">/g' /usr/local/lib/python3.6/site-packages/superset/templates/superset/basic.html
# RUN sed -i 's/\/static\/assets\/images\/favicon.png/\/assets\/img\/favicon.ico/g' /usr/local/lib/python3.6/site-packages/superset/templates/superset/basic.html
# RUN sed -i 's/<\/body>/<script src="\/public\/superset.js"><\/script><\/body>/g' /usr/local/lib/python3.6/site-packages/superset/templates/superset/basic.html
# RUN sed -i 's/<\/head>/<link rel="icon" href="\/assets\/img\/favicon.ico"><link rel="stylesheet" href="\/public\/superset.css" \/><\/head>/g' /usr/local/lib/python3.6/site-packages/superset/templates/superset/basic.html

# RUN sed -i 's/<head>/<head><link rel="icon" href="\/assets\/img\/favicon.ico">/g' /usr/local/lib/python3.6/site-packages/flask_appbuilder/templates/appbuilder/init.html
# RUN sed -i 's/\/static\/assets\/images\/favicon.png/\/assets\/img\/favicon.ico/g' /usr/local/lib/python3.6/site-packages/flask_appbuilder/templates/appbuilder/init.html
# RUN sed -i 's/<\/body>/<script src="\/public\/superset.js"><\/script><\/body>/g' /usr/local/lib/python3.6/site-packages/flask_appbuilder/templates/appbuilder/init.html
# RUN sed -i 's/<\/head>/<link rel="icon" href="\/assets\/img\/favicon.ico"><link rel="stylesheet" href="\/public\/superset.css" \/><\/head>/g' /usr/local/lib/python3.6/site-packages/flask_appbuilder/templates/appbuilder/init.html


ENTRYPOINT ["/entrypoint.sh"]

HEALTHCHECK CMD ["curl", "-f", "http://localhost:8088/health"]

EXPOSE 8088
