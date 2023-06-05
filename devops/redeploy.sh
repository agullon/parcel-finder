#!/bin/bash

DIR=$1
BRANCH=$2

pkill -f 'python3 telegram-app/main.py'

pushd $DIR

git checkout $BRANCH
git pull
python3 -m venv env
source env/bin/activate
pip install -r src/requirements.txt
python3 telegram-app/main.py | tee logs/$(date '+%Y%m%d_%H%M%S').log

popd
