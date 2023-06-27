# ska-pst-send

This project provides the Python library and applications for the SEND component of the Pulsar Timing instrument for SKA Mid and SKA Low.

## Documentation

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-pst-send/badge/?version=latest)](https://developer.skao.int/projects/ska-pst-send/en/latest/)

The documentation for this project, including the package description, Architecture description and the API modules can be found at SKA developer portal:  [https://developer.skao.int/projects/ska-pst-send/en/latest/](https://developer.skao.int/projects/ska-pst-send/en/latest/)

## Build Instructions
### Python application
Firstly clone this repo and submodules to your local file system

    git clone --recursive git@gitlab.com:ska-telescope/pst/ska-pst-send.git

then change to the newly cloned directory and create the build/ sub-directory

    cd ska-pst-send
    mkdir build

Create the builder image which will be used as the development environment for ska-pst-send

    make oci-build OCI_IMAGE=ska-pst-send-builder

To deploy a containerised development environment, execute the make target

    make local-dev-env

then enter the poetry shell

    poetry shell

To build the python package, execute the involved make target

    make python-build

### Documentaion

To build the `Read The Docs` documentaion, execute the following make target.

    make docs-build

## Testing

The python makefile library by the system team's pipeline machenry contains linting and testing tools.

To perform the lint tests, execute the involved make target

    make python-lint

To trigger SKA's python test harness, execute the involved make target

    make python-test

