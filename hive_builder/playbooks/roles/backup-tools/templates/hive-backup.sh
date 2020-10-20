#!/bin/bash
LOGGER=${0##*/}

function message () {
  echo "INFO: $LOGGER:" $*
}

function error () {
  echo "ERROR: $LOGGER:" $* 1>&2
  exit 1
}

mode=backup
services=$(/bin/ls /var/lib/hive-backup.d)
targets=$services

usage_exit() {
  error "Usage: $0 [-r] [-l service]"
}

function check_targets() {
  for target in $targets; do
    not_found=true
    for s in $services; do
      if [ $s == $target ]; then
        not_found=false
      fi
    done
    if $not_found; then
      error "backup scripts for $target is not available"
    fi
  done
}

while getopts rl:h OPT
do
  case $OPT in
    r)  mode=restore
      ;;
    l)  targets=${OPTARG//,/ }; check_targets
      ;;
    h)  usage_exit
      ;;
    \?) usage_exit
      ;;
  esac
done

if [ $# -ge $OPTIND ]; then
  usage_exit
fi

backupdir="{{ hive_home_dir }}/backup"
mkdir -p "$backupdir"
cd "$backupdir"

for service in $targets; do
  source /var/lib/hive-backup.d/${service}
  ${mode}_${service}
done
