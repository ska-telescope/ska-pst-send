# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the ScanManager."""

import pathlib
import pytest
from typing import List

from ska_pst_send import ScanManager, VoltageRecorderScan


def test_constructor(three_local_scans: List[VoltageRecorderScan], ss_id: str) -> None:

    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, ss_id)


def test_scan_paths(three_local_scans: List[VoltageRecorderScan], ss_id: str) -> None:

    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, ss_id)

    assert len(scan_manager._scans) == len(scan_list)

    scan_paths = scan_manager.get_scan_paths()
    for scan in scan_list:
        assert scan.full_scan_path in scan_paths

    relative_scan_paths = scan_manager.get_relative_scan_paths()
    for scan in scan_list:
        assert str(scan.relative_scan_path) in relative_scan_paths


def test_get_oldest_scan(three_local_scans: List[VoltageRecorderScan], ss_id: str):

    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, ss_id)

    oldest = scan_manager.get_oldest_scan()

    # for now, rely on the scan_manager to order the _scans attribute correctly
    assert oldest.relative_scan_path == scan_manager._scans[0].relative_scan_path
    assert oldest.data_product_path == scan_manager._scans[0].data_product_path
    assert oldest.full_scan_path == scan_manager._scans[0].full_scan_path
    assert oldest.get_all_files == scan_manager._scans[0].get_all_files


def test_delete_scan(three_local_scans: List[VoltageRecorderScan], ss_id: str):

    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, ss_id)

    time.sleep(0.1)
