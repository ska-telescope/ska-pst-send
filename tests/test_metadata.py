from ska.protosend.metadata import (
    PstConfig,
    PstContext,
    PstMetadata,
    PstObsCore,
)


def test_metadata_schema():
    pst_md = PstMetadata()
    for key in pst_md.config().to_dict().keys():
        assert key in PstConfig().to_dict().keys()

    for key in pst_md.context().to_dict().keys():
        assert key in PstContext().to_dict().keys()

    for key in pst_md.obscore().to_dict().keys():
        assert key in PstObsCore().to_dict().keys()


def test_metadata_field_objects():
    pst_md = PstMetadata()
    assert pst_md.config is PstConfig
    assert pst_md.context is PstContext
    assert pst_md.obscore is PstObsCore
