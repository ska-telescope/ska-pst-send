PROJECT = ska-pst-send

DOCS_SOURCEDIR=./docs/src

# This Makefile uses templates defined in the .make/ folder, which is a git submodule of
# https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile.

include .make/base.mk
include .make/oci.mk
include .make/python.mk

# common pst makefile library
include .pst/base.mk

# include your own private variables for custom deployment configuration
-include PrivateRules.mak

# PYTHON_RUNNER:= .venv/bin/python -m
PYTHON_LINT_TARGET:=src/ tests/
PYTHON_PUBLISH_URL:=https://artefact.skao.int/repository/pypi-internal/
PYTHON_SWITCHES_FOR_BLACK :=
PYTHON_SWITCHES_FOR_ISORT :=

DEV_IMAGE ?= artefact.skao.int/ska-pst-send-builder
DEV_TAG = `grep -m 1 -o '[0-9].*' .release`
SEND_BASE_IMAGE ?= library/ubuntu:22.04
PST_OCI_SEND_BUILDER_IMAGE ?= ska-pst-send-builder
PST_OCI_SEND_BUILDER_TAG ?= 0.0.4
PST_OCI_SEND_RUNTIME_IMAGE ?= library/ubuntu
PST_OCI_SEND_RUNTIME_TAG ?= 22.04
PST_OCI_STAT_RUNTIME_IMAGE ?= ska-pst-stat
PST_OCI_STAT_RUNTIME_TAG ?= 0.3.4

SKA_RELEASE_REGISTRY ?= artefact.skao.int
PST_DEV_REGISTRY ?= registry.gitlab.com/ska-telescope/pst

PST_OCI_STAT_REGISTRY ?= $(SKA_RELEASE_REGISTRY)
# in CI the CAR_OCI_REGISTRY_HOST can be overriden, local builds we want artefact.skao.int
PST_OCI_SEND_BUILDER_REGISTRY ?= $(CAR_OCI_REGISTRY_HOST)

# builder image always has to be from GitLab as its not pushed to CAR befuile runtime is built, so in a release build
PST_OCI_SEND_BUILDER ?= $(PST_OCI_SEND_BUILDER_REGISTRY)/$(PST_OCI_SEND_BUILDER_IMAGE):$(PST_OCI_SEND_BUILDER_TAG)
PST_OCI_SEND_RUNTIME ?= $(PST_OCI_SEND_RUNTIME_IMAGE):$(PST_OCI_SEND_RUNTIME_TAG)
PST_OCI_STAT_RUNTIME ?= $(PST_OCI_STAT_REGISTRY)/$(PST_OCI_STAT_RUNTIME_IMAGE):$(PST_OCI_STAT_RUNTIME_TAG)

OCI_BUILD_ADDITIONAL_ARGS	= --build-arg SEND_BASE_IMAGE=$(SEND_BASE_IMAGE) \
		--build-arg SEND_BUILDER=$(PST_OCI_SEND_BUILDER) \
		--build-arg SEND_RUNTIME=$(PST_OCI_SEND_RUNTIME) \
		--build-arg STAT_RUNTIME_IMAGE=$(PST_OCI_STAT_RUNTIME)

docs-pre-build:
	pip install -r docs/requirements.txt

# DEPENDENCIES INSTALLATION
.PHONY: local-pkg-install
PKG_CLI_CMD 		?=apt-get # Package manager executable
PKG_CLI_PAYLOAD 	?= 		# Payload file
PKG_CLI_PARAMETERS 	?= 	# Package manager installation parameters

local-pkg-install:
	$(PKG_CLI_CMD) $(PKG_CLI_PARAMETERS) `cat $(PKG_CLI_PAYLOAD)`

OCI_IMAGES = ska-pst-send-builder ska-pst-send
OCI_IMAGE_BUILD_CONTEXT= $(PWD)


# E203 and W503 conflict with black
PYTHON_TEST_FILE = tests
## Paths containing python to be formatted and linted
PYTHON_LINT_TARGET = src/ tests/
PYTHON_LINE_LENGTH = 110

PYTHON_SWITCHES_FOR_FLAKE8 = --extend-ignore=BLK,T --enable=DAR104 --ignore=E203,FS003,W503,N802 --max-complexity=10 \
    --rst-roles=py:attr,py:class,py:const,py:exc,py:func,py:meth,py:mod \
		--rst-directives deprecated,uml --exclude=src/ska_pst_lmc_proto
PYTHON_SWITCHES_FOR_BLACK = --force-exclude=src/ska_pst_lmc_proto
PYTHON_SWITCHES_FOR_ISORT = --skip-glob="*/__init__.py" --py 39 --thirdparty=ska_pst_lmc_proto
PYTHON_SWITCHES_FOR_PYLINT = --disable=W,C,R --ignored-modules="ska_pst_lmc_proto"
PYTHON_SWITCHES_FOR_AUTOFLAKE ?= --in-place --remove-unused-variables --remove-all-unused-imports --recursive --ignore-init-module-imports

mypy:
	$(PYTHON_RUNNER) mypy --config-file mypy.ini $(PYTHON_LINT_TARGET)

flake8:
	$(PYTHON_RUNNER) flake8 --show-source --statistics $(PYTHON_SWITCHES_FOR_FLAKE8) $(PYTHON_LINT_TARGET)

python-post-format:
	$(PYTHON_RUNNER) autoflake $(PYTHON_SWITCHES_FOR_AUTOFLAKE) $(PYTHON_LINT_TARGET)

python-post-lint: mypy

.PHONY: python-post-format, python-post-lint, mypy, flake8
