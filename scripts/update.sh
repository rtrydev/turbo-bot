#!/bin/bash

set -xe

git fetch origin

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
BASE=$(git merge-base @ @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "The repository is up-to-date."
elif [ "$LOCAL" = "$BASE" ]; then
    echo "There are updates available from remote!"
    git pull
    docker compose build && docker compose up -d
else
    echo "The local branch has diverged from the remote."
fi