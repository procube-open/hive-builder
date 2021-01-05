#!/bin/bash

service_list=$(systemctl list-unit-files --type service --no-pager --no-legend | awk '$2=="enabled" && $1 !~ "@" {print $1}' )

[[ -r /etc/zabbix/service_discovery_whitelist ]] && {
    service_list=$(echo "$service_list" | grep -E -f /etc/zabbix/service_discovery_whitelist)
}

[[ -r /etc/zabbix/service_discovery_blacklist ]] && {
    service_list=$(echo "$service_list" | grep -Ev -f /etc/zabbix/service_discovery_blacklist)
}

service_json='{"data":['
sepalator=''
for s in ${service_list}; do
  if systemctl show --property=Type $s | awk -F = '{print $2}' | egrep -qv '^(oneshot|dbus)'; then
    service_json="${service_json}${sepalator}{\"{#SERVICE}\": \"${s}\"}"
    sepalator=","
  fi
done
echo -n "${service_json}]}"
