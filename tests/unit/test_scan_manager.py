# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the ScanManager."""

from typing import List

from ska_pst_send import ScanManager, VoltageRecorderScan


def test_constructor(three_local_scans: List[VoltageRecorderScan], subsystem_id: str) -> None:
    """Test that the ScanManager constructor correctly initialises an object."""
    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, subsystem_id)
    assert len(scan_manager._scans) == len(scan_list)


def test_scan_paths(three_local_scans: List[VoltageRecorderScan], subsystem_id: str) -> None:
    """Test the ScanManager initialises with a scan list that matches the existing scans."""
    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, subsystem_id)

    scan_paths = scan_manager.scan_paths
    for scan in scan_list:
        assert scan.full_scan_path in scan_paths

    relative_scan_paths = scan_manager.relative_scan_paths
    for scan in scan_list:
        assert scan.relative_scan_path in relative_scan_paths


def test_oldest_scan(three_local_scans: List[VoltageRecorderScan], subsystem_id: str):
    """Test that ScanManager oldest_scan method."""
    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, subsystem_id)

    oldest = scan_manager.oldest_scan

    # for now, rely on the scan_manager to order the _scans attribute correctly
    assert oldest.relative_scan_path == scan_manager._scans[0].relative_scan_path
    assert oldest.data_product_path == scan_manager._scans[0].data_product_path
    assert oldest.full_scan_path == scan_manager._scans[0].full_scan_path
    assert oldest.get_all_files == scan_manager._scans[0].get_all_files


def test_delete_scan(three_local_scans: List[VoltageRecorderScan], subsystem_id: str):
    """Test the ScanManager detects scans that have been processed and deleted."""
    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, subsystem_id)

    scan_manager._refresh_scans()
    assert len(scan_manager._scans) == len(scan_list)

    # delete the scans in the list, and force the scan_manager to detect this
    for i in range(len(scan_list)):

        # delete the files in the specified scan in the list, noting it does not delete the scan
        scan_manager._scans[0].delete_scan()

        # force the scan_manager to detect the deleted scan
        oldest = scan_manager.oldest_scan
        assert len(scan_manager._scans) == len(scan_list) - (i + 1)

        if (i + 1) < len(scan_list):
            assert oldest.relative_scan_path == scan_manager._scans[0].relative_scan_path
            assert oldest.data_product_path == scan_manager._scans[0].data_product_path
            assert oldest.full_scan_path == scan_manager._scans[0].full_scan_path
            assert oldest.get_all_files == scan_manager._scans[0].get_all_files
        else:
            assert oldest is None

    scan_manager._refresh_scans()
    assert len(scan_manager._scans) == 0
    assert scan_manager.oldest_scan is None
