#!/bin/sh
#
# Generate the API schema from the code into the output file.
#
# Run this script from the root of the repository:
#
#   ./bin/generate_api_schema.sh [outfile]
#
# 'outfile' defaults to `src/opendms/api/openapi.yml`
#
# For multiple API specifications (different components or multiple major versions),
# take a look at the Open Zaak configuration.
#
set -e

OUTFILE=${1:-src/opendms/api/openapi.yaml}

echo "Generating OAS schema"
src/manage.py spectacular \
    --validate \
    --fail-on-warn \
    --lang=en \
    --file "$OUTFILE"

echo "Done."
