#!/usr/bin/env bash

datetime () { date +"%Y-%m-%d %H:%M:%S"; }

[[ -t 1 ]] && interm=yes

red ()    { echo "\e[1;31m$1\e[m"; }
yellow () { echo "\e[1;33m$1\e[m"; }
log () { printf "$(yellow "[log $(datetime)]") $1\n"; }
err () { printf "$(red "[error $(datetime)]") $1\n"; exit 1; }

ci_path="$CI_PROJECT_DIR"
test_path="$ci_path/$CI_JOB_TOKEN"

#
# print status
#

#system=clariden
#uarch=a100
#uenv=gromacs:2023

log "system=$system; uarch=$uarch; uenv=$uenv"

#
# create temporary working path
#
tmp_path=/tmp/uenv-tmp/$CI_JOB_TOKEN
rm -rf $tmp_path
mkdir -p $tmp_path

log "temporary path $tmp_path"

#
# set up python environment
#
pyenv_path=$tmp_path/.pyenv

python3 -m venv $pyenv_path
source $pyenv_path/bin/activate
log "created and loaded python venv in $pyenv_path"
log "$(python --version)"

pip install --upgrade --quiet pip
pip install --quiet -r ./config/requirements.txt
log "installed python dependencies"

./config/ci.py
[[ $? -eq 0  ]] || err "unable to configure"

log "configuration complete"

log "the following pipeline was generated"
cat pipeline.yml
