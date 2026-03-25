import json
import subprocess

FILE = "docker/open-zaak/fixtures/open_zaak_fixtures.json"

# All FkOrServiceUrlField fields in OpenZaak, when dumping data, instead of storing the FK
# of the object or the service, just store the service name as a string. This causes errors when
# trying to load the fixture, so these fields are temporarily removed/disabled in the fixture.

fields_to_skip = {
    "zaken.zaak": ["zaaktype"],
    "zaken.status": ["statustype"],
    "zaken.resultaat": ["resultaattype"],
    "zaken.rol": ["roltype"],
    "zaken.zaakinformatieobject": ["informatieobject"],
    "documenten.enkelvoudiginformatieobject": ["informatieobjecttype"],
    "documenten.objectinformatieobject": ["zaak"],
}

cmd = [
    "docker",
    "compose",
    "-f",
    "docker/docker-compose.open-zaak.yml",
    "run",
    "openzaak-web.local",
    "python",
    "src/manage.py",
    "dumpdata",
    "--indent=4",
    "--output",
    "/app/fixtures/open_zaak_fixtures.json",
    "authorizations.applicatie",
    "vng_api_common.jwtsecret",
    "config.featureflags",
    "catalogi",
    "zaken",
    "documenten",
]

result = subprocess.run(cmd, text=True)

# Read file
with open(FILE) as f:
    data = json.load(f)
    for obj in data:
        if obj["model"] in fields_to_skip:
            model = obj["model"]
            for field in fields_to_skip[model]:
                obj["fields"].pop(field, None)

# Save file
with open(FILE, "w") as file:
    json.dump(data, file, indent=2)
