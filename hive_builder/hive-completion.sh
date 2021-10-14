#!/bin/sh
_hive(){
local cur=${COMP_WORDS[COMP_CWORD]}
local prev=${COMP_WORDS[COMP_CWORD-1]}
  if [ ${COMP_CWORD} -ge 2 ]; then
    local pprev=${COMP_WORDS[COMP_CWORD-2]}
  else
    local pprev=${COMP_WORDS[0]}
  fi
  subc="build-infra setup-hosts build-images build-volumes build-networks deploy-services initialize-services all inventory init set ssh install-collection list-hosts list-services list-volumes get-install-dir setup-bash-completion"
  if [ "${prev}" = "hive" ]; then
    COMPREPLY=( $(compgen -W "${subc}" -- "${cur}") )
  elif [ "${pprev}" = "ssh" -a "${prev}" = "-t" ]; then
    COMPREPLY=( $(compgen -W "$(hive list-hosts)" -- "${cur}") )
  elif [ "${pprev}" = "build-volumes" -a "${prev}" = "-l" ]; then
    COMPREPLY=( $(compgen -W "$(hive list-volumes)" -- "${cur}") )
  elif [ "${pprev}" = "build-images" -o "${pprev}" = "deploy-services" -o "${pprev}" = "initialize-services" -a "${prev}" = "-l" ]; then
    COMPREPLY=( $(compgen -W "$(hive list-services)" -- "${cur}") )
  fi
} &&
complete -F _hive hive
