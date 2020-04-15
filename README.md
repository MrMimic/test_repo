# test_repo
Repo allowing to add external tools to this git

## Dependencies

Dependencies will be handled with [Poetry](https://python-poetry.org/docs/).

    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

To start working:

    poetry new <PACKAGE>

To add dependencies:

    poetry add <DEP>

To install / update dependencies:

    poetry install / update

To build:

    poetry build


## Continuous Integration

TravisCI