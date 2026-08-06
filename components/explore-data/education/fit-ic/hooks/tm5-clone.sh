#!/bin/bash

TARGET="/home/jovyan/tm5"
REPO="https://github.com/gmonteil/tm5.git"
BRANCH="ilab"

if [[ -d "$TARGET" ]]; then
    echo "tm5-clone: $TARGET already present, skipping clone"
else
    echo "tm5-clone: cloning $REPO ($BRANCH) into $TARGET..."
    git clone --branch "$BRANCH" "$REPO" "$TARGET"
fi

echo "tm5-clone: installing $TARGET in editable mode..."
uv pip install --system -e "$TARGET"
