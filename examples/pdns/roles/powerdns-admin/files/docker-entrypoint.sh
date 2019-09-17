#!/usr/bin/env sh

[ -n "$DEBUG" ] && [ "$DEBUG" -gt 0 ] && set -x && echo "LOG_LEVEL = 'DEBUG'" >> config.py

env | grep '^PDA_' | while read varname
do
  varname=${varname/=*/}
  echo "${varname/PDA_/} =  os.environ.get('${varname}')" >> config.py
done

set -eo pipefail

# default values
if [[ -z ${PDNS_PROTO} ]];
 then PDNS_PROTO="http"
fi

if [[ -z ${PDNS_PORT} ]];
 then PDNS_PORT=8081
fi
if [[ -z ${DB_DATA_DIR} ]];
 then DB_DATA_DIR=/powerdns-admin/data
fi
DB_DATA=$DB_DATA_DIR/padmin.sqlite
mkdir -p "$DB_DATA_DIR"

if [ ! -f "$DB_DATA" ]; then
  echo "===> Initialize DB"
  cp /initdb/padmin.sqlite $DB_DATA
  ./create_admin.py administrator "${PDNS_API_KEY}"
fi

echo "===> Update PDNS API connection info"
# initial setting if not available in the DB
sqlite3 $DB_DATA "INSERT INTO setting (name, value) SELECT * FROM (SELECT 'pdns_api_url', '${PDNS_PROTO}://${PDNS_HOST}:${PDNS_PORT}') AS tmp WHERE NOT EXISTS (SELECT name FROM setting WHERE name = 'pdns_api_url') LIMIT 1;"
sqlite3 $DB_DATA "INSERT INTO setting (name, value) SELECT * FROM (SELECT 'pdns_api_key', '${PDNS_API_KEY}') AS tmp WHERE NOT EXISTS (SELECT name FROM setting WHERE name = 'pdns_api_key') LIMIT 1;"
sqlite3 $DB_DATA "INSERT INTO setting (name, value) SELECT * FROM (SELECT 'signup_enabled', 'False') AS tmp WHERE NOT EXISTS (SELECT name FROM setting WHERE name = 'signup_enabled') LIMIT 1;"

# update pdns api setting if .env is changed.
echo "===> Update PDNS API connection info"
sqlite3 $DB_DATA "UPDATE setting SET value='${PDNS_PROTO}://${PDNS_HOST}:${PDNS_PORT}' WHERE name='pdns_api_url';"
sqlite3 $DB_DATA "UPDATE setting SET value='${PDNS_API_KEY}' WHERE name='pdns_api_key';"
sqlite3 $DB_DATA "UPDATE setting SET value='False' WHERE name='signup_enabled';"

chown www-data:www-data -R $DB_DATA_DIR

exec "$@"
