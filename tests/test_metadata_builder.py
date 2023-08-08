import os

from ska.protosend.metadata import (
    PstConfig,
    PstContext,
    PstMetadata,
    PstObsCore,
)
from ska.protosend.metadata_builder import MetaDataBuilder


def test_metadata_schema():
    pst_mdb = MetaDataBuilder()
    assert type(pst_mdb.pst_metadata) is PstMetadata


"""
TODO: test read and compare data from header or weights file
TODO: test contents of context
TODO: test contents of config
TODO: test contents of obscore
TODO: test compute values involving multiple dada files
TODO: test write, read, load generated yaml file
"""

def test_write_metadata():
    pst_mdb = MetaDataBuilder()
    pst_mdb.dsp_mount_path = "/tmp/"

    pst_context = PstContext(
                    observer="jdoe",
                    intent="Tied-array beam observation of J1921+2153",
                    notes="notes TBD"
                )
    pst_config = PstConfig(
                    image="artefact.skao.int/ska-pst/ska-pst",
                    version="0.1.3"
                )
    pst_obscore = PstObsCore(dataproduct_type="timeseries",
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
                    o_ucd="null"
                )

    pst_mdb.pst_metadata.context = pst_context
    pst_mdb.pst_metadata.config = pst_config
    pst_mdb.pst_metadata.obscore = pst_obscore

    file_name = "ska-data-product.yaml"
    pst_mdb.write_metadata(file_name=file_name)

    absolute_path = f"{pst_mdb.dsp_mount_path}/ska-data-product.yaml"

    assert os.path.exists(absolute_path)
