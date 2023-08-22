# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Tests for the PstMetaData class."""
from ska_pst_send.metadata import PstConfig, PstContext, PstMetaData, PstObsCore


def test_metadata_field_objects():
    """Test the property is of the correct object type."""
    pst_md = PstMetaData()
    assert type(pst_md.config) is PstConfig
    assert type(pst_md.context) is PstContext
    assert type(pst_md.obscore) is PstObsCore
