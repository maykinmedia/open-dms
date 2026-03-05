#!/bin/bash
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-opendms-flower}"

exec celery --app opendms --workdir src flower
