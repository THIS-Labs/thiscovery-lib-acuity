# thiscovery-lib-acuity

![Code coverage](coverage.svg)

![feature](https://github.com/THIS-Labs/thiscovery-liv-acuity/actions/workflows/feature.yaml/badge.svg)

![release](https://github.com/THIS-Labs/thiscovery-liv-acuity/actions/workflows/release.yaml/badge.svg)

## Installation

This library should not be deployed. Instead, it should be installed using `pip`
into the env of other stacks.

Run the command:

`pip install https://github.com/THIS-Labs/thiscovery-lib-acuity/archive/main.zip`

## Code coverage

    export TEST_ON_AWS=False
    export TEST_CALENDAR_EMAIL=<put email here>
    export PYTHONPATH=./tests:$PYTHONPATH
    coverage run -m unittest discover tests && coverage html && coverage-badge > coverage.svg