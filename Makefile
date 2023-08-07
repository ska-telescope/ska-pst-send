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

DEV_IMAGE					?=artefact.skao.int/ska-pst-send-builder
DEV_TAG						=`grep -m 1 -o '[0-9].*' .release`
SEND_BASE_IMAGE				:=library/ubuntu:22.04
PST_OCI_SEND_BUILDER_IMAGE	:=ska-pst-send-builder
PST_OCI_SEND_BUILDER_TAG	:=0.0.0
PST_OCI_SEND_BUILDER		:=$(PST_OCI_SEND_BUILDER_IMAGE):$(PST_OCI_SEND_BUILDER_TAG)
PST_OCI_SEND_RUNTIME_IMAGE	:=library/ubuntu
PST_OCI_SEND_RUNTIME_TAG	:=22.04
PST_SEND_OCI_RUNTIME		:=$(PST_OCI_SEND_RUNTIME_IMAGE):$(PST_OCI_SEND_RUNTIME_TAG)
OCI_BUILD_ADDITIONAL_ARGS	= --build-arg SEND_BASE_IMAGE=$(SEND_BASE_IMAGE) --build-arg SEND_BUILDER=$(PST_OCI_SEND_BUILDER) --build-arg SEND_RUNTIME=$(PST_SEND_OCI_RUNTIME)

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