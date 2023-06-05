#!/bin/bash

SCRIPT_PATH=$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)

DIR="/home/agullon/parcel-finder/"
BRANCH="main"

git fetch
	
REMOTE_COMMIT_ID=$(git log origin/$BRANCH -1 --format="%H")
LOCAL_COMMIT_ID=$(git log $BRANCH -1 --format="%H")

NUM_PID_RUNNING=$(pgrep -fxc 'python3 src/main.py')

if (( $NUM_PID_RUNNING != 1 )) || [ "$REMOTE_COMMIT_ID" != "$LOCAL_COMMIT_ID" ]; then
	bash /home/agullon/parcel-finder/devops/redeploy.sh $DIR $BRANCH
fi

