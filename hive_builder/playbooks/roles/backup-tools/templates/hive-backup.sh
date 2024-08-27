#!/bin/bash
LOGGER=${0##*/}

. ~/docker/bin/activate

function message () {
  echo "INFO: $LOGGER:" "$*"
}

function error () {
  echo "ERROR: $LOGGER:" $* 1>&2
  exit 1
}

mode=backup
services=$(/bin/ls /var/lib/hive-backup.d)
services="hive-zabbix hive-registry ${services}"
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
  if [ ${service} = "hive-zabbix" ]; then
    function backup_hive-zabbix() {
      message "ENTER SERVICE hive-zabbix for BACKUP"
      # for backup hive-zabbix
      backup_file="backup-hive-zabbix-$(date +%Y%m%d%H%M%S).sql.gz"
      message "START backup hive-zabbix into $backup_file":
      if (cd {{ hive_home_dir }}/zabbix/;docker compose exec -T zabbix-db sh -c 'mysqldump -u zabbix -pzabbix zabbix --single-transaction | gzip') > "$backup_file"; then
        message "END backup for hive-zabbix into $backup_file"
        message "LINK backup-hive-zabbix-latest.sql.gz to $backup_file"
        rm -f "backup-hive-zabbix-latest.sql.gz"
        ln -s "$backup_file" "backup-hive-zabbix-latest.sql.gz"
      else
        message "FAIL backup for hive-zabbix"
      fi
      message "Clean up old files than {{ hive_zabbix_backup_cleanup_days_before }} like backup-hive-zabbix-*.sql.gz"
      find ./ -name "backup-hive-zabbix-*.sql.gz" -daystart -mtime +{{ hive_zabbix_backup_cleanup_days_before }} -type f | xargs rm -f
      message "LEAVE SERVICE hive-zabbix for BACKUP"
    }
    function restore_hive-zabbix() {
      message "ENTER SERVICE hive-zabbix for RESTORE"
      # for restore hive-zabbix
      backup_file="backup-hive-zabbix-latest.sql.gz"
      if [ -r $backup_file ]; then
        message "START restore for hive-zabbix from $backup_file"
        cp "$backup_file" {{ hive_home_dir }}/zabbix/"$backup_file";
        cd {{ hive_home_dir }}/zabbix;
        docker cp "$backup_file" $(docker compose ps -q zabbix-db):/root/today.sql.gz
        if docker compose exec -T zabbix-db sh -c 'zcat /root/today.sql.gz | mysql -B -u zabbix -pzabbix -D zabbix'; then
          message "END restore for hive-zabbix"
        else
          message "FAIL restore for hive-zabbix"
        fi
      else
        message "SKIP restore for hive-zabbix which does not have backup-hive-zabbix-latest"
      fi
      message "LEAVE SERVICE hive-zabbix for RESTORE"
      }
  ${mode}_${service}
  cd "$backupdir"
  elif [ ${service} = "hive-registry" ]; then
    function backup_hive-registry() {
      message "ENTER SERVICE hive-registry for BACKUP"
      # for backup hive-registry
      backup_file="backup-hive-registry-$(date +%Y%m%d%H%M%S).tar.gz"
      message "START backup hive-registry into $backup_file":
      if (cd {{ hive_home_dir }}/registry/;docker compose exec -T registry_server sh -c 'cd /var/lib/registry; tar czf - $(find . -maxdepth 1 -not -name .)') > "$backup_file"; then
        message "END backup for hive-registry into $backup_file"
        message "LINK backup-hive-registry-latest.tar.gz to $backup_file"
        rm -f "backup-hive-registry-latest.tar.gz"
        ln -s "$backup_file" "backup-hive-registry-latest.tar.gz"
      else
        message "FAIL backup for hive-registry"
      fi
      message "Clean up old files than {{ hive_registry_backup_cleanup_days_before }} like backup-hive-registry-*.tar.gz"
      find ./ -name "backup-hive-registry-*.tar.gz" -daystart -mtime +{{ hive_registry_backup_cleanup_days_before }} -type f | xargs rm -f
      message "LEAVE SERVICE hive-registry for BACKUP"
    }
    function restore_hive-registry() {
      message "ENTER SERVICE hive-registry for RESTORE"
      # for restore hive-registry
      backup_file="backup-hive-registry-latest.tar.gz"
      if [ -r $backup_file ]; then
        message "START restore for hive-registry from $backup_file"
        cp "$backup_file" {{ hive_home_dir }}/registry/"$backup_file";
        cd {{ hive_home_dir }}/registry;
        docker cp "$backup_file" $(docker compose ps -q registry_server):/root/today.tar.gz
        if docker compose exec -T registry_server sh -c 'cd /var/lib/registry; rm -rf $(find . -maxdepth 1 -not -name .); tar xzf /root/today.tar.gz'; then
          message "END restore for hive-registry"
        else
          message "FAIL restore for hive-registry"
        fi
      else
        message "SKIP restore for hive-registry which does not have backup-hive-registry-latest"
      fi
      message "LEAVE SERVICE hive-registry for RESTORE"
      }
  ${mode}_${service}
  cd "$backupdir"
  else
  source /var/lib/hive-backup.d/${service}
  ${mode}_${service}
  cd "$backupdir"
  fi
done
