# logging functions
mysql_log() {
	local type="$1"; shift
	# accept argument string or stdin
	local text="$*"; if [ "$#" -eq 0 ]; then text="$(cat)"; fi
	local dt; dt="$(date -Iseconds)"
	printf '%s [%s] [Entrypoint]: %s\n' "$dt" "$type" "$text"
}
mysql_note() {
	mysql_log Note "$@"
}
mysql_warn() {
	mysql_log Warn "$@" >&2
}
mysql_error() {
	mysql_log ERROR "$@" >&2
	exit 1
}

_mysql_passfile() {
	# echo the password to the "file" the client uses
	# the client command will use process substitution to create a file on the fly
	# ie: --defaults-extra-file=<( _mysql_passfile )
    cat <<-EOF
        [client]
        password="`cat /run/secrets/root-password`"
	EOF
    # note use of tab character above
}

# Execute sql script, passed via stdin
#    ie: docker_process_sql <<<'INSERT ...'
#    ie: docker_process_sql <my-file.sql
docker_process_sql() {
    # default mysql but caller can override
	mariadb --defaults-extra-file=<( _mysql_passfile) -uroot -hdb --comments --database=mysql "$@"
}

