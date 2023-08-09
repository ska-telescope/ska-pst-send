# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Tests for the MetaDataBuilder class."""
import os

import yaml

from ska.protosend.metadata import PstConfig, PstContext, PstFiles, PstMetaData, PstObsCore
from ska.protosend.metadata_builder import MetaDataBuilder


def test_metadata_schema():
    """Test the property is of the correct object type."""
    pst_mdb = MetaDataBuilder()
    assert type(pst_mdb.pst_metadata) is PstMetaData


"""
TODO: test read and compare data from header or weights file
TODO: test contents of context
TODO: test contents of config
TODO: test contents of obscore
TODO: test compute values involving multiple dada files
"""

pst_context = PstContext(
    observer="jdoe",
    intent="Tied-array beam observation of J1921+2153",
    notes="notes TBD",
)
pst_config = PstConfig(image="artefact.skao.int/ska-pst/ska-pst", version="0.1.3")
pst_files = [
    PstFiles(
        description="Channelised voltage data raw files",
        path="data",
        size="343326720",
        status="done",
    ),
    PstFiles(
        description="Channelised voltage weights raw files",
        path="weights",
        size="2954496",
        status="done",
    ),
]
pst_obscore = PstObsCore(
    dataproduct_type="timeseries",
    dataproduct_subtype="voltages",
    calib_level=0,
    obs_id=485,
    access_estsize=343277568,
    target_name="J1921+2153",
    s_ra=19.362448611111116,
    s_dec=1.4589333333333332,
    t_min="40587",
    t_max="40587.00000000229920260608196258544921875",
    t_resolution=0.00020736000000000002,
    t_exptime=207.36,
    facility_name="SKA-Observatory",
    instrument_name="SKA-LOW",
    pol_xel=2,
    pol_states="null",
    em_xel=432,
    em_unit="Hz",
    em_min=999218750.0,
    em_max=1000781250.0,
    em_res_power="null",
    em_resolution=3616.8981481481483,
    o_ucd="null",
)


def test_write_metadata():
    """Test writing metadata dictionary into yaml file."""
    pst_mdb = MetaDataBuilder()
    pst_mdb.dsp_mount_path = "/tmp/"

    pst_mdb.pst_metadata.interface = "http://schema.skao.int/ska-data-product-meta/0.1"
    pst_mdb.pst_metadata.execution_block = "eb-19700101-485"
    pst_mdb.pst_metadata.files = pst_files
    pst_mdb.pst_metadata.context = pst_context
    pst_mdb.pst_metadata.config = pst_config
    pst_mdb.pst_metadata.obscore = pst_obscore

    file_name = "ska-data-product.yaml"
    pst_mdb.write_metadata(file_name=file_name)

    absolute_path = f"{pst_mdb.dsp_mount_path}/ska-data-product.yaml"

    assert os.path.exists(absolute_path)

    with open(absolute_path, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)

    # Update the properties of the metadata object with loaded data
    assert data.get("interface") == pst_mdb.pst_metadata.interface
    assert data.get("execution_block") == pst_mdb.pst_metadata.execution_block
    # Data files
    assert data.get("files")[0]["description"] == pst_mdb.pst_metadata.files[0].description
    assert data.get("files")[0]["path"] == pst_mdb.pst_metadata.files[0].path
    assert data.get("files")[0]["size"] == pst_mdb.pst_metadata.files[0].size
    assert data.get("files")[0]["status"] == pst_mdb.pst_metadata.files[0].status
    # Weights files
    assert data.get("files")[1]["description"] == pst_mdb.pst_metadata.files[1].description
    assert data.get("files")[1]["path"] == pst_mdb.pst_metadata.files[1].path
    assert data.get("files")[1]["size"] == pst_mdb.pst_metadata.files[1].size
    assert data.get("files")[1]["status"] == pst_mdb.pst_metadata.files[1].status

    assert data.get("obscore")["dataproduct_type"] == pst_mdb.pst_metadata.obscore.dataproduct_type
    assert data.get("obscore")["dataproduct_subtype"] == pst_mdb.pst_metadata.obscore.dataproduct_subtype
    assert data.get("obscore")["calib_level"] == pst_mdb.pst_metadata.obscore.calib_level
    assert data.get("obscore")["obs_id"] == pst_mdb.pst_metadata.obscore.obs_id
    assert data.get("obscore")["access_estsize"] == pst_mdb.pst_metadata.obscore.access_estsize
    assert data.get("obscore")["target_name"] == pst_mdb.pst_metadata.obscore.target_name
    assert data.get("obscore")["s_ra"] == pst_mdb.pst_metadata.obscore.s_ra
    assert data.get("obscore")["s_dec"] == pst_mdb.pst_metadata.obscore.s_dec
    assert data.get("obscore")["t_min"] == pst_mdb.pst_metadata.obscore.t_min
    assert data.get("obscore")["t_max"] == pst_mdb.pst_metadata.obscore.t_max
    assert data.get("obscore")["t_resolution"] == pst_mdb.pst_metadata.obscore.t_resolution
    assert data.get("obscore")["t_exptime"] == pst_mdb.pst_metadata.obscore.t_exptime
    assert data.get("obscore")["facility_name"] == pst_mdb.pst_metadata.obscore.facility_name
    assert data.get("obscore")["instrument_name"] == pst_mdb.pst_metadata.obscore.instrument_name
    assert data.get("obscore")["pol_xel"] == pst_mdb.pst_metadata.obscore.pol_xel
    assert data.get("obscore")["pol_states"] == pst_mdb.pst_metadata.obscore.pol_states
    assert data.get("obscore")["em_xel"] == pst_mdb.pst_metadata.obscore.em_xel
    assert data.get("obscore")["em_unit"] == pst_mdb.pst_metadata.obscore.em_unit
    assert data.get("obscore")["em_min"] == pst_mdb.pst_metadata.obscore.em_min
    assert data.get("obscore")["em_max"] == pst_mdb.pst_metadata.obscore.em_max
    assert data.get("obscore")["em_res_power"] == pst_mdb.pst_metadata.obscore.em_res_power
    assert data.get("obscore")["em_resolution"] == pst_mdb.pst_metadata.obscore.em_resolution
    assert data.get("obscore")["o_ucd"] == pst_mdb.pst_metadata.obscore.o_ucd
