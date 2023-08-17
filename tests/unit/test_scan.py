# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the scans."""

import pathlib

import pytest

from ska_pst_send.scan import Scan
from tests.conftest import create_scan, remove_product


def test_constructor(local_product_path: pathlib.Path, scan_path: pathlib.Path) -> None:
    try:
        scan = create_scan(local_product_path, scan_path)
        assert scan.scan_config_file_exists == False
        assert scan.is_scan_recording == True
        assert scan.data_product_file_exists == False
        assert scan.is_scan_completed == False
    except Exception as exc:
        import traceback

        traceback.print_exc()
    finally:
        remove_product(local_product_path)


def test_scan_parameters(scan: Scan) -> None:

    assert scan.scan_config_file_exists
    assert scan.is_scan_recording == True
    assert scan.data_product_file_exists == False
    assert scan.is_scan_completed == False

    # manually create the ska-data-product.yaml file
    scan._data_product_file.touch()
    assert scan.data_product_file_exists

    # manually create the scan_completed file
    scan._scan_completed_file.touch()
    assert scan.is_scan_recording == False
    assert scan.is_scan_completed

def test_scan_delete(scan: Scan) -> None:

   scan.delete()