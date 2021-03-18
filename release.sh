#!/bin/bash

usage() {
  echo "Usage: $0 -C -n -m" 1>&2
  echo "-f : force do even if working tree is dirty" 1>&2
  echo "-C : dry run" 1>&2
  echo "-a : release as alpha version" 1>&2
  echo "-b : release as beta version" 1>&2
  echo "-r : release as release candidate version" 1>&2
  echo "-s : release as official version" 1>&2
  echo "-t : release to test pypi repository" 1>&2
  echo "-o : release to official repository" 1>&2
  echo "-n : do not push to github" 1>&2
}

error_usage_exit() {
  echo "Error: $1"
  usage
  exit 2
}

error_exit() {
  echo "Error: $1"
  exit 1
}

NO_FORCE=true
DRY_RUN=false
SERIES=
DEPLOY_TARGET=
GIT_PUSH=true

# parse args
while getopts fCabrstonh OPT
do
  case $OPT in
    f)  NO_FORCE=false
        ;;
    C)  DRY_RUN=true
        ;;
    a|b|r|s)  if [[ "${SERIES}" != "" ]]; then
          error_usage_exit "cannot specify more than one option(-a, -b, -r, -s) to specify the release series"
        fi
        SERIES=$OPT
        ;;
    t|o)  if [[ "${DEPLOY_TARGET}" != "" ]]; then
          error_usage_exit "cannot specify more than one option(-t, -o) to specify the deployment target"
        fi
        DEPLOY_TARGET=$OPT
        ;;
    n)  GIT_PUSH=false
        ;;
    h)  usage
        exit 0
        ;;
    \?) error_usage_exit "unknown option ${OPT}"
        ;;
  esac
done

shift $((OPTIND - 1))

if [ $# -ne 0 ]; then
  error_usage_exit "cannot specify arguments: $*"
fi

# gather status
if ! STATUS=$(git status -z 2>&1); then
  error_exit "fail to get status: $STATUS"
fi
if [[ "$STATUS" != "" ]] && ${NO_FORCE}; then
  error_exit "working directory is not clean: $X"
fi
if ! GIT_TAG=$(git describe --tags 2>&1); then
  error_exit "fail to describe tags: $GIT_TAG"
fi
if ! DEFAULT_BRANCH=$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}' 2>&1); then
  error_exit "fail to get default branch: $DEFAULT_BRANCH"
fi
if ! BRANCH=$(git rev-parse --abbrev-ref @ 2>&1); then
  error_exit "fail to get current branch: $BRANCH"
fi
if ! SETUP_VERSION=$(pipenv run version 2>&1); then
  error_exit "fail to get default version: pipenv run version -> $DEFAULT_VERSION"
fi
VERSION=${SETUP_VERSION%.dev*}
IFS=. REVISIONS=(${VERSION})
IFS=" "
REVISION=${REVISIONS[${#REVISIONS[@]}-1]}
NO_SERIES_VERSION=${VERSION}
NUMBER_ONLY='^[0-9]+$'
if [[ $REVISION =~ $NUMBER_ONLY ]]; then
  DEFAULT_SERIES=a
  VERSION=${VERSION}a0
else
  case $REVISION in
    *a*) DEFAULT_SERIES=a
       NO_SERIES_VERSION=${VERSION%a*};;
    *b*) DEFAULT_SERIES=b
       NO_SERIES_VERSION=${VERSION%b*};;
    *rc*) DEFAULT_SERIES=r
       NO_SERIES_VERSION=${VERSION%rc*};;
    *) error_exit "fail to parse revision: $REVISION"
  esac
fi

# set defaults
if [[ "${SERIES}" == "" ]]; then
  SERIES=$DEFAULT_SERIES
elif [[ "${SERIES}" > "$DEFAULT_SERIES" ]]; then
  echo "Step up series to $SERIES from $DEFAULT_SERIES"
  case $SERIES in
    a|b) VERSION="${NO_SERIES_VERSION}${SERIES}0";;
    r) VERSION="${NO_SERIES_VERSION}rc0";;
    s) VERSION="${NO_SERIES_VERSION}";;
  esac
elif [[ "${SERIES}" < "$DEFAULT_SERIES" ]]; then
  error_exit "cannot step down series to $SERIES from $DEFAULT_SERIES"
fi
if ! CHECK_RESULT=$(pipenv run check-version $VERSION 2>&1); then
  error_exit "version $VERSION is not canonical according to Pep 440: $CHECK_RESULT"
fi

if [[ "$VERSION" == "$GIT_TAG" ]]; then
  error_exit "the target version $SETUP_VERSION is already tagged"
fi


if [[ "${DEPLOY_TARGET}" == "" ]]; then
  case $SERIES in
    a|b) DEPLOY_TARGET=t;;
    r|s) DEPLOY_TARGET=o;;
  esac
fi

case $SERIES in
  a|b) if [[ "$BRANCH" == "$DEFAULT_BRANCH" ]]; then
      echo "WARN: $SEREIS revision is released from default branch."
    fi
    ;;
  r|s) if [[ "$BRANCH" != "$DEFAULT_BRANCH" ]]; then
      echo "WARN: $SEREIS revision is released from non default branch."
    fi
    ;;
esac

if [[ $DEPLOY_TARGET == "t" ]]; then
  DEPLOY_SCRIPT=test-deploy
else
  DEPLOY_SCRIPT=deploy
fi

echo "start release $VERSION(DEPLOY_SCRIPT=$DEPLOY_SCRIPT) from BRANCH:$BRANCH"

if $DRY_RUN; then
  echo "git tag $VERSION"
  echo pipenv run clean
  echo pipenv run build
  echo pipenv run "$DEPLOY_SCRIPT"
  if $GIT_PUSH; then
    echo git push --tags origin "$BRANCH"
  fi
else
  set -x
  git tag "$VERSION"
  pipenv run clean
  pipenv run build
  pipenv run "$DEPLOY_SCRIPT"
  set +x
  if $GIT_PUSH; then
    set -x
    git push --tags origin "$BRANCH"
    set +x
  fi
fi
