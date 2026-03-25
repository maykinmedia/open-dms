# Open Zaak

The `docker-compose.open-zaak.yml` compose file is available to run an instance of Open Zaak.

## docker compose

Start an instance in your local environment from the parent directory:

```bash
docker compose -f docker/docker-compose.open-zaak.yml up -d
```

This brings up the admin at http://localhost:8003/admin/. You can log in with the `admin` / `admin`
credentials.

## Load fixtures

The fixtures in `open-zaak/fixtures` are automatically loaded when the Open Zaak container starts.

## Dump fixtures

Whenever you make changes in the admin for the tests, you need to dump the fixtures again so that
bringing up the containers the next time (or in other developers' environments) will still have the
same data.

Dump the fixtures with (in the `docker` directory):

```bash

python docker/open-zaak/fixtures/custom_dumpdata.py

```

Load data


```bash

docker compose -f docker/docker-compose.open-zaak.yml run openzaak-web.local python src/manage.py loaddata /app/fixtures/open_zaak_fixtures.json

```

Depending on your OS, you may need to grant extra write permissions:

```bash
chmod o+rwx ./open-zaak/fixtures
```
