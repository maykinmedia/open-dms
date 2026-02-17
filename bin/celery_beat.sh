#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-opendms-scheduler}"

mkdir -p celerybeat

echo "Starting celery beat"
exec celery beat \
    --app opendms \
    -l $LOGLEVEL \
    --workdir src \
    -s ../celerybeat/beat
