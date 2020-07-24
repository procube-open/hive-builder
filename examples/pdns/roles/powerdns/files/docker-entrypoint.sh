#!/usr/bin/env sh

[ -n "$DEBUG" ] && [ "$DEBUG" -gt 0 ] && set -x

set -eo pipefail

check_service() {
        local service=$1
        local port=$2
        echo "check service: start for $service:$port"
        local count=${MYSQL_CHECK_RETRY:-10}
        local interval=${MYSQL_CHECK_INTERVAL:-4}
        set +eo pipefail
        while ! nc -w 1 -z $service $port >& /dev/null
        do
                count=$(( $count - 1 ))
                if [ $count -eq 0 ]; then
                        break
                fi
                sleep $interval
                echo "check service: retry check $service:$port interval=$interval rest=$count"
        done
        set -eo pipefail
        if [ $count -eq 0 ]; then
                echo "check service: exceed max retry count ${MYSQL_CHECK_RETRY:-10}"
                return 1
        fi
        echo "check service: check success $service:$port"
        return 0
}

# if command starts with an option, prepend pdns_server
if [ "${1:0:1}" = '-' ]; then
	set -- pdns_server "$@"
fi

if [ $1 == 'pdns_server' ]; then
	check_service "${MYSQL_HOST}" "${MYSQL_PORT:-3306}"
fi

echo gmysql-host=${MYSQL_HOST} >> /etc/pdns/pdns.conf
echo gmysql-port=${MYSQL_PORT:-3306} >> /etc/pdns/pdns.conf
echo gmysql-dbname=${MYSQL_DBNAME:-powerdns} >> /etc/pdns/pdns.conf
echo gmysql-user=${MYSQL_USER:-powerdns} >> /etc/pdns/pdns.conf
echo gmysql-group=${MYSQL_GROUP:-client} >> /etc/pdns/pdns.conf
echo gmysql-password=${MYSQL_PASSWORD} >> /etc/pdns/pdns.conf
echo gmysql-dnssec=${MYSQL_DNSSEC:-no} >> /etc/pdns/pdns.conf
echo gmysql-innodb-read-committed=${MYSQL_INNODB_READ_COMMITTED:-yes} >> /etc/pdns/pdns.conf
echo gmysql-timeout=${MYSQL_TIMEOUT:-10} >> /etc/pdns/pdns.conf

# avoid exit at 'read varname' read EOF
set +eo pipefail
env | grep '^PDNSCONF_' | while read varname
do
	varname=${varname/=*/}
	paramname=$(echo ${varname/PDNSCONF_/} | tr '[:upper:]_' '[:lower:]-')
  sed -r -i "s/^[# ]*${paramname}=.*\$/${paramname}=$(eval echo \$$varname)/g" /etc/pdns/pdns.conf
done
# exec 4
exec "$@"
