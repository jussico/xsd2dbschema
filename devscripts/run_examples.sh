#!/bin/bash

function run {
    echo "$@"
    $@
}

run python3 xsd2dbschema.py examples/sample.xsd
run python3 xsd2dbschema.py examples/sample-2.xsd

run python3 xsd2dbschema.py -h

# fail as an example
run python3 xsd2dbschema.py 

# fails
curl -o examples/alto-3-0.xsd 'https://www.loc.gov/standards/alto/v3/alto-3-0.xsd'
run python3 xsd2dbschema.py examples/alto-3-0.xsd
