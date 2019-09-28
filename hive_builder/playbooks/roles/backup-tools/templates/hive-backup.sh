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
{% set hive_safe_targets = groups['services'] | intersect(groups[hive_stage]) | map('extract', hostvars) | selectattr('hive_backup_scripts', 'defined') | map(attribute='inventory_hostname') | list %}
services='{{ hive_safe_targets | join(' ') }}'
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

export DOCKER_HOST={{ groups['first_hive'] | intersect(groups[hive_stage]) | first }}:2376
export DOCKER_TLS=1

{% for hive_safe_target in hive_safe_targets %}
{% set hive_safe_backup_scripts = hostvars[hive_safe_target].hive_backup_scripts %}
function backup_{{ hive_safe_target }}() {
  message "ENTER SERVICE {{ hive_safe_target }} for BACKUP"
  {%- for hive_safe_backup_script in hive_safe_backup_scripts %}
    {%- if hive_safe_backup_script.batch_scripts is defined %}
      {%- for batch_script in hive_safe_backup_script.batch_scripts %}

  message "START batch: {{ batch_script }}"
  if dexec -n {{ hive_safe_target }} sh -c '{{ batch_script }}' 1>&2 ; then
    message "END batch: {{ batch_script }}"
  else
    message "FAIL batch: {{ batch_script }}"
  fi
      {%- endfor %}
    {%- endif %}
    {%- if hive_safe_backup_script.backup_command is defined or  hive_safe_backup_script.directory is defined %}

  # for backup {{ hive_safe_backup_script.name }}
  backup_file="backup-{{ hive_safe_backup_script.name }}-$(date +%Y%m%d%H%M%S).{{ hive_safe_backup_script.ext | default('tar.gz')}}"
  message "START backup {{ hive_safe_backup_script.name }} into $backup_file"
      {%- if hive_safe_backup_script.backup_command is defined %}
        {%- if hive_safe_backup_script.backup_file is defined %}

  if dexec -n {{ hive_safe_target }} sh -c '{{ hive_safe_backup_script.backup_command }}' 1>&2 ; then
    dcp {{ hive_safe_target }}:{{ hive_safe_backup_script.backup_file }} $backup_file
        {%- else %}

  if dexec -n {{ hive_safe_target }} sh -c '{{ hive_safe_backup_script.backup_command }}' > "$backup_file"; then
        {%- endif %}
        {%- elif hive_safe_backup_script.directory is defined %}

  if dexec -n {{ hive_safe_target }} sh -c 'cd {{hive_safe_backup_script.directory}}; tar czf - $(find . -maxdepth 1 -not -name .)' > "$backup_file"; then
      {%- endif %}

    message "END backup for {{ hive_safe_backup_script.name }} into $backup_file"
    message "LINK backup-{{ hive_safe_backup_script.name }}-latest.{{ hive_safe_backup_script.ext | default('tar.gz')}} to $backup_file"
    rm -f "backup-{{ hive_safe_backup_script.name }}-latest.{{ hive_safe_backup_script.ext | default('tar.gz')}}"
    ln -s "$backup_file" "backup-{{ hive_safe_backup_script.name }}-latest.{{ hive_safe_backup_script.ext | default('tar.gz')}}"
  else
    message "FAIL backup for host {{ hive_safe_backup_script.name }}"
  fi
    {%- endif %}
    {%- if hive_safe_backup_script.cleanup_days_before is defined %}

  message "Clean up old files than {{ hive_safe_backup_script.cleanup_days_before }} like backup-{{ hive_safe_backup_script.name }}-*.{{ hive_safe_backup_script.ext | default('tar.gz')}}"
  find ./ -name "backup-{{ hive_safe_backup_script.name }}-*.{{ hive_safe_backup_script.ext | default('tar.gz')}}" -mtime +{{ hive_safe_backup_script.cleanup_days_before }} -type f | xargs rm -f
    {%- endif %}
  {%- endfor %}

  message "LEAVE SERVICE {{ hive_safe_target }} for BACKUP"
}

function restore_{{ hive_safe_target }}() {
  message "ENTER SERVICE {{ hive_safe_target }} for RESTORE"
  {%- for hive_safe_backup_script in hive_safe_backup_scripts %}
    {%- if hive_safe_backup_script.backup_command is defined or  hive_safe_backup_script.directory is defined %}

  # for restore {{ hive_safe_backup_script.name }}
  backup_file="backup-{{ hive_safe_backup_script.name }}-latest.{{ hive_safe_backup_script.ext | default('tar.gz') }}"
  if [ -r $backup_file ]; then
    message "START restore for {{ hive_safe_backup_script.name }} from $backup_file"
      {%- if hive_safe_backup_script.restore_command is defined %}
        {%- if hive_safe_backup_script.restore_file is defined %}

    dcp -L $backup_file {{ hive_safe_target }}:{{ hive_safe_backup_script.restore_file }}
    if dexec -n {{ hive_safe_target }} sh -c '{{ hive_safe_backup_script.restore_command }}'  ; then
        {%- else %}

    if dexec -n {{ hive_safe_target }} sh -c '{{ hive_safe_backup_script.restore_command }}'  < $backup_file; then
        {%- endif %}
        {%- elif hive_safe_backup_script.directory is defined %}

    dcp -L $backup_file {{ hive_safe_target }}:/tmp/restore.tar.gz
    if dexec -n {{ hive_safe_target }} sh -c 'cd {{hive_safe_backup_script.directory}}; rm -rf $(find . -maxdepth 1 -not -name .); tar xzf /tmp/restore.tar.gz'; then
      {%- endif %}

      message "END restore for {{ hive_safe_backup_script.name }}"
    else
      message "FAIL restore for {{ hive_safe_backup_script.name }}"
    fi
  else
    message "SKIP restore for {{ hive_safe_backup_script.name }} which does not have backup-{{ hive_safe_backup_script.name }}-latest"
  fi
    {%- endif %}

  message "LEAVE SERVICE {{ hive_safe_target }} for RESTORE"
  {%- endfor %}

}
{% endfor %}

backupdir="{{ hive_home_dir }}/backup"
mkdir -p "$backupdir"
cd "$backupdir"

for service in $targets; do
  ${mode}_${service}
done
