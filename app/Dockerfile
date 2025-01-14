ARG PYTHON_VER

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:${PYTHON_VER}-alpine

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# set the working directory in the container
WORKDIR /app

# Install pip requirements
COPY requirements.txt .

# special configuration for mysql client - https://stackoverflow.com/a/78683658
COPY client.my.cnf /home/appuser/.my.cnf

# needed for mysqlclient package to compile
# adapted from https://github.com/gliderlabs/docker-alpine/issues/181#issuecomment-444857401
#   and https://github.com/gliderlabs/docker-alpine/issues/181#issuecomment-348608168
RUN apk add --no-cache mariadb-connector-c-dev \
    && apk add --no-cache --virtual .build-deps \
        build-base \
        mariadb-dev \
    && pip install -r requirements.txt \
    && rm -rf .cache/pip \
    && apk del .build-deps

# we'll be doing mysql, mysqldump commands
RUN apk add --no-cache mysql-client

# use msmtp for sendmail, need volume with /etc/msmtprc defined
RUN apk add --no-cache msmtp && rm /usr/sbin/sendmail && ln -s /usr/bin/msmtp /usr/sbin/sendmail

# we're going to want to use bash
RUN apk add bash

# add cron stuff for appuser execution
COPY cronjobs /etc/crontabs/appuser

# copy the content of the local src directory to the working directory
# this isn't needed when developing as there's a bind under volumes: in the docker-compose.dev.yml file
COPY src .

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN chmod +x /app/dbupgrade_and_run.sh && adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser
