#!/bin/bash
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-opendrc-flower}"

exec celery flower --app opendrc --workdir src
