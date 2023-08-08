"""Tests for the ska_python_skeleton module."""
from ska.protosend.metadata import PstMetadata
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
