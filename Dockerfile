# This is a multi-stage build file, which means a stage is used to build
# the backend (dependencies), the frontend stack and a final production
# stage re-using assets from the build stages. This keeps the final production
# image minimal in size.

# Stage 1 - Backend build environment
# includes compilers and build tooling to create the environment
FROM python:3.14-slim-bookworm AS backend-build

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
        pkg-config \
        build-essential \
        # only relevant when using editable/github dependencies, which is discouraged
        # git \
        libpq-dev \
        shared-mime-info \
        # required for (log) routing support in uwsgi
        libpcre3 \
        libpcre3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir /app/src

# Ensure we use the latest version of pip
RUN pip install pip setuptools -U
COPY ./requirements /app/requirements
RUN pip install -r requirements/production.txt


# Stage 2 - Build the Front end
FROM node:24-bullseye-slim AS frontend-build

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
  git \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY ./src/opendms/frontend .
RUN npm ci
RUN npm run build


# Stage 3 - Build docker image suitable for production
FROM python:3.14-slim-bookworm

# Stage 3.1 - Set up the needed production dependencies
# install all the dependencies for GeoDjango
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
        procps \
        nano \
        mime-support \
        postgresql-client \
        gettext \
        shared-mime-info \
        libpcre3 \
        # lxml deps
        # libxslt \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./bin/docker_start.sh /start.sh
COPY ./bin/uwsgi.ini \
    # Uncomment if you use celery
    # ./bin/celery_worker.sh \
    # ./bin/celery_beat.sh \
    # ./bin/celery_flower.sh \
    /

RUN mkdir /app/bin /app/log /app/media

VOLUME ["/app/log", "/app/media"]

# copy backend build deps
COPY --from=backend-build /usr/local/lib/python3.14 /usr/local/lib/python3.14
COPY --from=backend-build /usr/local/bin/uwsgi /usr/local/bin/uwsgi
COPY --from=backend-build /usr/local/bin/maykin-common /usr/local/bin/maykin-common
# Uncomment if you use celery
# COPY --from=backend-build /usr/local/bin/celery /usr/local/bin/celery
COPY --from=backend-build /app/src/ /app/src/

# copy frontend build statics
COPY --from=frontend-build /app/dist /app/src/opendms/frontend


# copy source code
COPY ./src /app/src

RUN groupadd -g 1000 maykin \
    && useradd -M -u 1000 -g 1000 maykin \
    && chown -R maykin:maykin /app

# drop privileges
USER maykin

ARG COMMIT_HASH RELEASE=latest
ENV RELEASE=${RELEASE} \
    GIT_SHA=${COMMIT_HASH} \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=opendms.conf.docker

ARG SECRET_KEY=dummy OTEL_SDK_DISABLED=true

LABEL org.label-schema.vcs-ref=$COMMIT_HASH \
      org.label-schema.vcs-url="https://github.com/maykinmedia/opendms" \
      org.label-schema.version=$RELEASE \
      org.label-schema.name="opendms"

# Run collectstatic and compilemessages, so the result is already included in
# the image
RUN python src/manage.py collectstatic --noinput \
    && python src/manage.py compilemessages

EXPOSE 8000
CMD ["/start.sh"]
