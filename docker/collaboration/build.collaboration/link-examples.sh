#!/bin/bash
# Jupyter "before-notebook.d" startup hook (sourced at every container launch).
#
# The image bakes read-only example notebooks at /opt/icos-examples. We expose
# them to the user at ~/icos-examples. Because the collab service gives each
# user a PERSISTENT home directory, copying would duplicate the examples per
# user and drift across image versions. Instead we SYMLINK to the single,
# image-provided copy: one version, read-only, no wasted storage. Users who
# want to experiment copy a notebook into their own writable home themselves.
#
# NOTE: strict mode (set -euo pipefail) is deliberately omitted — a failure
# here must not abort the container startup sequence.

TARGET=/opt/icos-examples
LINK="$HOME/icos-examples"

# Idempotent: only (re)create the link if it isn't already the correct symlink.
# This also repairs a stale regular directory left by a previous copy-based
# image, or a symlink pointing somewhere else.
if [ "$(readlink "$LINK")" != "$TARGET" ]; then
    rm -rf "$LINK"
    ln -s "$TARGET" "$LINK"
fi
