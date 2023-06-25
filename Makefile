PROJECT = ska-pst-send

DOCS_SOURCEDIR=./docs/src

# This Makefile uses templates defined in the .make/ folder, which is a git submodule of
# https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile.

-include .make/docs.mk
-include .make/help.mk
-include .make/oci.mk
-include .make/python.mk
-include .make/release.mk

# common pst makefile library
-include .pst/base.mk

# include your own private variables for custom deployment configuration
-include PrivateRules.mak

DEV_IMAGE	?=registry.gitlab.com/ska-telescope/pst/ska-pst-smrb/ska-pst-smrb-builder
DEV_TAG		?=0.8.7

# PYTHON_RUNNER:= .venv/bin/python -m
PYTHON_LINT_TARGET:=src/ tests/
PYTHON_PUBLISH_URL:=https://artefact.skao.int/repository/pypi-internal/
PYTHON_SWITCHES_FOR_BLACK :=
PYTHON_SWITCHES_FOR_ISORT :=

PST_SMRB_OCI_REGISTRY		?=registry.gitlab.com/ska-telescope/pst/ska-pst-smrb
SMRB_RUNTIME_IMAGE			?=${PST_SMRB_OCI_REGISTRY}/ska-pst-smrb
SEND_BUILDER_IMAGE			?=${PST_SMRB_OCI_REGISTRY}/ska-pst-smrb-builder
SEND_RUNTIME_IMAGE			?=ubuntu:22.04
PST_SMRB_OCI_COMMON_TAG		?=${DEV_TAG}
OCI_BUILD_ADDITIONAL_ARGS	=--build-arg SMRB_RUNTIME_IMAGE=${SMRB_RUNTIME_IMAGE}:${PST_SMRB_OCI_COMMON_TAG} --build-arg SEND_BUILDER_IMAGE=${SEND_BUILDER_IMAGE}:${PST_SMRB_OCI_COMMON_TAG} --build-arg SEND_RUNTIME_IMAGE=${SEND_RUNTIME_IMAGE}

python-pre-lint:
	pip install isort black flake8 pylint-junit pytest build

docs-pre-build:
	pip install breathe exhale
	apt install -y doxygen