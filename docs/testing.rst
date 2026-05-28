.. _testing:

=======
Testing
=======


Prerequisites
=============

Most tests require PostgreSQL and Redis.
If you don't have them running already, start them with Docker Compose::

    docker compose up -d db redis


Backend tests
=============

Run all tests::

    python src/manage.py test src

Run a single test::

    python src/manage.py test src/opendms/api/tests/test_documents.py::DocumentTests::test_detail


(re-)recording VCR cassettes
-----------------------------

Tests in ``search_index/`` and ``api/tests/`` use
`VCR cassettes <https://maykin-django-common.readthedocs.io/en/latest/reference/vcr.html>`_
to record and replay HTTP interactions against Elasticsearch and Open Zaak
respectively. Cassettes live under ``src/opendms/*/tests/files/vcr_cassettes/``.

To (re-)record, start the required containers:

* **Elasticsearch** (``search_index/`` tests, ``localhost:9201``)::

    docker compose -f docker/docker-compose.es.yml up -d

* **Open Zaak** (``api/tests/`` Zaak tests, ``localhost:8003``)::

    docker compose -f docker/docker-compose.open-zaak.yml up -d

Then delete the cassette YAML file you want to re-record and re-run the test.
In development ``VCR_RECORD_MODE`` defaults to ``once``, so missing cassettes
are recorded automatically and existing ones are replayed.

See `docker/open-zaak/README.md <https://github.com/maykinmedia/open-dms/blob/main/docker/open-zaak/README.md>`_ for Open Zaak fixture management.


Frontend tests
==============

From ``src/opendms/frontend/``::

    npm install
    npm test

Lint and type-check::

    npm lint
    npm check-types


Coverage
========

Run with coverage and generate a report::

    coverage run src/manage.py test src
    coverage html

The report is written to ``htmlcov/index.html``. Ready to open with your browser.


CI
==

GitHub Actions runs tests against PostgreSQL 14–17 with Redis. See ``.github/workflows/ci.yml``.
