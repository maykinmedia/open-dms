#!/bin/sh

set -ex

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

fixtures_dir=${FIXTURES_DIR:-/app/fixtures}

mountpoint=${SUBPATH:-/}

# Copy static root to volume, if required
if [ -n "$STATIC_ROOT_VOLUME" ]; then
    cp -r /app/static/* "$STATIC_ROOT_VOLUME"
fi

# Wait for the database container
# See: https://docs.docker.com/compose/startup-order/
export PGHOST=${DB_HOST:-db}
export PGPORT=${DB_PORT:-5432}
until pg_isready; do
  >&2 echo "Waiting for database connection..."
  sleep 1
done
>&2 echo "Database is up."

# Set defaults for OTEL
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-opendms}"

# Apply database migrations
>&2 echo "Apply database migrations"
OTEL_SDK_DISABLED=True python src/manage.py migrate

# multi-process/multi-thread is necessary for concurrency if there's no reverse proxy
# like nginx sitting in front of uwsgi
export UWSGI_PROCESSES=${UWSGI_PROCESSES:-4}
export UWSGI_THREADS=${UWSGI_THREADS:-1}

# Periodically recycle workers - recover memory in the event of memory leaks
export UWSGI_MAX_REQUESTS=${UWSGI_MAX_REQUESTS:-1000}

# Start server
>&2 echo "Starting server"
exec uwsgi \
    --strict \
    --ini "${SCRIPTPATH}/uwsgi.ini" \
    --http :8000 \
    --http-keepalive \
    --mount $mountpoint=opendms.wsgi:application \
    --manage-script-name \
    --static-map /static=/app/static \
    --static-map /media=/app/media  \
    --chdir src \
    --enable-threads \
    --master \
    --single-interpreter \
    --die-on-term \
    --need-app \
    --post-buffering=8192 \
    --buffer-size=65535
