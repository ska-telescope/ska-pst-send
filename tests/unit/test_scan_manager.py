# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the ScanManager."""

import logging
import random
import time
from typing import List

from ska_pst_send import ScanManager, VoltageRecorderScan
from ska_pst_send.voltage_recorder_scan import NANOSECONDS_PER_SEC


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


def test_oldest_scan(three_local_scans: List[VoltageRecorderScan], subsystem_id: str) -> None:
    """Test that ScanManager oldest_scan method."""
    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    scan_manager = ScanManager(data_product_path, subsystem_id)

    oldest = scan_manager.next_unprocessed_scan()

    # for now, rely on the scan_manager to order the _scans attribute correctly
    assert oldest is not None, "Expected oldest scan to not be None"
    assert oldest.relative_scan_path == scan_manager._scans[0].relative_scan_path
    assert oldest.data_product_path == scan_manager._scans[0].data_product_path
    assert oldest.full_scan_path == scan_manager._scans[0].full_scan_path
    assert oldest.get_all_files == scan_manager._scans[0].get_all_files


def test_delete_scan(three_local_scans: List[VoltageRecorderScan], subsystem_id: str) -> None:
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
        oldest = scan_manager.next_unprocessed_scan()
        assert len(scan_manager._scans) == len(scan_list) - (i + 1)

        if (i + 1) < len(scan_list):
            assert oldest is not None, "Expected oldest scan to not be None"
            assert oldest.relative_scan_path == scan_manager._scans[0].relative_scan_path
            assert oldest.data_product_path == scan_manager._scans[0].data_product_path
            assert oldest.full_scan_path == scan_manager._scans[0].full_scan_path
            assert oldest.get_all_files == scan_manager._scans[0].get_all_files
        else:
            assert oldest is None

    scan_manager._refresh_scans()
    assert len(scan_manager._scans) == 0
    assert scan_manager.next_unprocessed_scan() is None


def test_next_unprocessed_scan_gets_scan_with_earliest_modified_time(
    three_local_scans: List[VoltageRecorderScan], subsystem_id: str
) -> None:
    """Test scan manager returns oldest scan if all are active."""
    scan_list = three_local_scans
    data_product_path = scan_list[0].data_product_path
    random.shuffle(scan_list)

    scan_offset_ns: int = int(30 * NANOSECONDS_PER_SEC)
    now_ns = time.time_ns()
    for (idx, s) in enumerate(scan_list):
        s._modified_time_ns = now_ns - idx * scan_offset_ns

    expected_scan = scan_list[-1]

    # shuffle again
    random.shuffle(scan_list)
    scan_manager = ScanManager(data_product_path, subsystem_id)
    scan_manager._scans = scan_list

    actual_scan = scan_manager.next_unprocessed_scan()
    assert expected_scan == actual_scan, "Expected scan that had the earliest modified time"


def test_next_unprocessed_scan_gets_only_active_scans_if_multiple_scans(
    three_local_scans: List[VoltageRecorderScan], subsystem_id: str
) -> None:
    """Test scan manager returns oldest active scan, ignoring in inactive scans."""
    scan_list = [*three_local_scans]
    data_product_path = scan_list[0].data_product_path
    random.shuffle(scan_list)

    scan_timeout_sec = 10
    scan_timeout_ns: int = int(scan_timeout_sec * NANOSECONDS_PER_SEC)

    now_ns = time.time_ns()

    # setup a modified time earlier than active modified time
    # this sets up 2 inactive scans
    for (idx, s) in enumerate(scan_list[:-2]):
        s._modified_time_ns = now_ns - (idx + 2) * scan_timeout_ns

    expected_scan = scan_list[-1]

    # shuffle again
    random.shuffle(scan_list)
    scan_manager = ScanManager(data_product_path, subsystem_id, scan_timeout=scan_timeout_sec)
    scan_manager._scans = scan_list

    actual_scan = scan_manager.next_unprocessed_scan()
    assert expected_scan == actual_scan, "Expected scan that had the earliest modified time"


def test_next_unprocessed_scan_gets_oldest_inactive_scan_if_no_active_scan(
    three_local_scans: List[VoltageRecorderScan], subsystem_id: str, logger: logging.Logger
) -> None:
    """Test scan manager returns oldest inactive scan if no active scans available."""
    scan_list = [*three_local_scans]
    data_product_path = scan_list[0].data_product_path
    random.shuffle(scan_list)

    scan_timeout_sec = 10
    scan_timeout_ns: int = int(scan_timeout_sec * NANOSECONDS_PER_SEC)

    now_ns = time.time_ns()

    # setup a modified time earlier than active modified time
    # all scans are modified before active time
    for (idx, s) in enumerate(scan_list):
        s._modified_time_ns = now_ns - (idx + 2) * scan_timeout_ns

    for s in scan_list:
        logger.info(f"{s} has modified time of {s.modified_time_secs}")

    expected_scan = scan_list[-1]

    # shuffle again
    random.shuffle(scan_list)

    scan_manager = ScanManager(data_product_path, subsystem_id, scan_timeout=scan_timeout_sec)
    scan_manager._scans = scan_list

    actual_scan = scan_manager.next_unprocessed_scan()
    assert expected_scan == actual_scan, "Expected scan that had the earliest modified time"
