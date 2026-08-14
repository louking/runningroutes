#!/bin/bash

source ./app-initdb.d/sql-commands.sh

# NOTE: file end of line characters must be LF, not CRLF (see https://stackoverflow.com/a/58220487/799921)

# create database if necessary
while ! ./app-initdb.d/create-database.sh
do
    sleep 5
done

# look for sql file, should only be one, delete after loading sql into database
files=(/initdb.d/${APP_DATABASE}-*.sql)
[ -f "$files" ] && ((${#files[@]}==1)) && docker_process_sql --database=${APP_DATABASE} <$files && rm $files

flask db upgrade

exec "$@"
