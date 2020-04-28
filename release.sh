#!/bin/bash

usage_exit() {
        echo "Usage: $0 -f -n -m" 1>&2
        echo "-f : force do even if working tree is dirty or last commit has diestance from last tag" 1>&2
        echo "-m : do release to master" 1>&2
        echo "-n : do not push to github" 1>&2
        exit 1
}

NO_FORCE=true
RELEASE_BRANCE=develop
GIT_PUSH=true
DEPLOY_SCRIPT=test-deploy

while getopts fhmn OPT
do
  case $OPT in
    f)  NO_FORCE=false
        ;;
    m)  RELEASE_BRANCE=master
        DEPLOY_SCRIPT=deploy
        ;;
    n)  GIT_PUSH=false
        ;;
    h)  usage_exit
        ;;
    \?) usage_exit
        ;;
  esac
done

shift $((OPTIND - 1))

if [ $# -ne 0 ]; then
  usage_exit
fi

if [ "$(git symbolic-ref --short HEAD)" != "develop" ]; then
  echo ERROR: current branch is not develop
  exit 1
fi

VERSION=$(git describe --tags)

if $NO_FORCE && [[ "$VERSION" == *-* ]]; then
  echo "ERROR: tree is not clean or has distance from last tag: version=$VERSION"
  exit 1
fi

echo start release $VERSION
set -ex
if [ "$RELEASE_BRANCE" == "master" ]; then
  git checkout master
  git merge "$VERSION"
fi
pipenv run clean
pipenv run build
pipenv run "$DEPLOY_SCRIPT"
if $GIT_PUSH; then
  git push --tags origin "$RELEASE_BRANCE"
fi
if [ "$RELEASE_BRANCE" == "master" ]; then
  git checkout develop
fi
