# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the scans."""

import pathlib

from ska_pst_send import Scan
from tests.conftest import create_scan, remove_send_tempdir


def test_constructor(local_product_path: pathlib.Path, scan_path: pathlib.Path) -> None:
    """Test the Scan constructor correctly initialises an object."""
    try:
        scan = create_scan(local_product_path, scan_path)
        assert scan.scan_config_file_exists is False
        assert scan.is_recording
        assert scan.data_product_file_exists is False
        assert scan.is_complete is False
    finally:
        remove_send_tempdir()


def test_scan_parameters(scan: Scan) -> None:
    """Test the Scan properties return the expected values base on file system control files."""
    assert scan.scan_config_file_exists
    assert scan.is_recording
    assert scan.data_product_file_exists is False
    assert scan.is_complete is False

    # manually create the ska-data-product.yaml file
    scan._data_product_file.touch()
    assert scan.data_product_file_exists

    # manually create the scan_completed file
    scan._scan_completed_file.touch()
    assert scan.is_recording is False
    assert scan.is_complete


def test_delete_scan(scan: Scan) -> None:
    """Test the Scan delete_scan method."""
    assert scan.data_product_path.exists()
    assert scan.full_scan_path.exists()
    scan.delete_scan()
    assert scan.data_product_path.exists()
    assert scan.full_scan_path.exists() is False


def test_delete_multiple_scans(scan_factory: Scan) -> None:
    """Test that Deleting multiple scans works as corrected with directory tree pruning."""
    scan1 = scan_factory()
    scan2 = scan_factory()

    # delete the first scan and assert that the second scan remains
    scan1.delete_scan()
    assert scan1.data_product_path.exists()
    assert scan1.full_scan_path.exists() is False
    assert scan2.full_scan_path.exists()

    # delete the second scan and assert that it is gone
    scan2.delete_scan()
    assert scan2.data_product_path.exists()
    assert scan2.full_scan_path.exists() is False

    # check the data product path for both scans is now empty
    count = 0
    for child in scan1.data_product_path.iterdir():
        count += 1
    assert count == 0

    remove_send_tempdir()
