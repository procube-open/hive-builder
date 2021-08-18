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
services="zabbix registry ${services}"
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
  if [ ${service} = "zabbix" ]; then
    function backup_zabbix() {
      message "ENTER SERVICE zabbix for BACKUP"
      # for backup zabbix
      backup_file="backup-zabbix-$(date +%Y%m%d%H%M%S).sql.gz"
      message "START backup zabbix into $backup_file":
      if (cd /home/admin/zabbix/;docker-compose exec -T zabbix-db sh -c 'mysqldump -u zabbix -pzabbix zabbix | gzip') > "$backup_file"; then
        message "END backup for zabbix into $backup_file"
        message "LINK backup-zabbix-latest.sql.gz to $backup_file"
        rm -f "backup-zabbix-latest.sql.gz"
        ln -s "$backup_file" "backup-zabbix-latest.sql.gz"
      else
        message "FAIL backup for zabbix"
      fi
      message "Clean up old files than 10 like backup-zabbix-*.sql.gz"
      find ./ -name "backup-zabbix-*.sql.gz" -mtime +10 -type f | xargs rm -f
      message "LEAVE SERVICE zabbix for BACKUP"
    }
    function restore_zabbix() {
      message "ENTER SERVICE zabbix for RESTORE"
      # for restore zabbix
      backup_file="backup-zabbix-latest.sql.gz"
      if [ -r $backup_file ]; then
        message "START restore for zabbix from $backup_file"
        cp "$backup_file" /home/admin/zabbix/"$backup_file";
        cd /home/admin/zabbix;
        docker cp "$backup_file" $(docker-compose ps -q zabbix-db):/root/today.sql.gz
        if docker-compose exec -T zabbix-db sh -c 'zcat /root/today.sql.gz | mysql -B -u zabbix -pzabbix -D zabbix'; then
          message "END restore for zabbix"
        else
          message "FAIL restore for zabbix"
        fi
      else
        message "SKIP restore for zabbix which does not have backup-zabbix-latest"
      fi
      message "LEAVE SERVICE zabbix for RESTORE"
      }
  ${mode}_${service}
  elif [ ${service} = "registry" ]; then
    function backup_registry() {
      message "ENTER SERVICE registry for BACKUP"
      # for backup registry
      backup_file="backup-registry-$(date +%Y%m%d%H%M%S).tar.gz"
      message "START backup registry into $backup_file":
      if (cd /home/admin/registry/;docker-compose exec -T registry_server sh -c 'cd /var/lib/registry; tar czf - $(find . -maxdepth 1 -not -name .)') > "$backup_file"; then
        message "END backup for registry into $backup_file"
        message "LINK backup-registry-latest.tar.gz to $backup_file"
        rm -f "backup-registry-latest.tar.gz"
        ln -s "$backup_file" "backup-registry-latest.tar.gz"
      else
        message "FAIL backup for registry"
      fi
      message "Clean up old files than 10 like backup-registry-*.tar.gz"
      find ./ -name "backup-registry-*.tar.gz" -mtime +10 -type f | xargs rm -f
      message "LEAVE SERVICE registry for BACKUP"
    }
    function restore_registry() {
      message "ENTER SERVICE registry for RESTORE"
      # for restore registry
      backup_file="backup-registry-latest.tar.gz"
      if [ -r $backup_file ]; then
        message "START restore for registry from $backup_file"
        cp "$backup_file" /home/admin/registry/"$backup_file";
        cd /home/admin/registry;
        docker cp "$backup_file" $(docker-compose ps -q registry_server):/root/today.tar.gz
        if docker-compose exec -T registry_server sh -c 'cd /var/lib/registry; rm -rf $(find . -maxdepth 1 -not -name .); tar xzf /root/today.tar.gz'; then
          message "END restore for registry"
        else
          message "FAIL restore for registry"
        fi
      else
        message "SKIP restore for registry which does not have backup-registry-latest"
      fi
      message "LEAVE SERVICE registry for RESTORE"
      }
  ${mode}_${service}
  else
  source /var/lib/hive-backup.d/${service}
  ${mode}_${service}
  fi
done

