#!/bin/bash

DIR=$1
BRANCH=$2

pushd $DIR

make stop-parcel-finder
make stop-selenium-hub
sleep 10

git checkout $BRANCH
git pull

make build
make run-parcel-finder
make run-selenium-hub

popd
