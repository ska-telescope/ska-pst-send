# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the scan transfer thread."""

import threading
import time
from typing import List, Tuple

from ska_pst_send import ScanTransfer, VoltageRecorderScan


def test_constructor(local_remote_scans: Tuple[VoltageRecorderScan, VoltageRecorderScan]) -> None:
    """Test the ScanTransfer construction initialises the object correctly."""
    (local_scan, remote_scan) = local_remote_scans

    cond = threading.Condition()
    scan_transfer = ScanTransfer(local_scan, remote_scan, cond)
    assert scan_transfer.completed is False
    assert scan_transfer.is_alive() is False


def test_transfer(
    local_remote_scans: Tuple[VoltageRecorderScan, VoltageRecorderScan], scan_files: List[str]
) -> None:
    """Test the ScanTransfer can fully transfer a completed scan."""
    (local_scan, remote_scan) = local_remote_scans

    # expected length is the number of scan_files + 1 (for the scan_configuration.json file)
    expected_length = len(scan_files) + 1
    assert len(local_scan.get_all_files()) == expected_length
    assert len(remote_scan.get_all_files()) == 0

    cond = threading.Condition()
    scan_transfer = ScanTransfer(local_scan, remote_scan, cond, loop_wait=0.1, minimum_age=0)
    scan_transfer.start()

    assert scan_transfer.is_alive()

    # wait some time for the ScanTransfer to transfer the data files
    time.sleep(0.1)

    local_scan._scan_completed_file.touch()
    local_scan._data_product_file.touch()

    # busy wait for the scan to be transferred
    while scan_transfer.is_alive():
        time.sleep(0.5)

    assert scan_transfer.completed
    scan_transfer.join()

    assert len(remote_scan.get_all_files()) == len(local_scan.get_all_files())


def test_aborted_transfer(
    local_remote_scans: Tuple[VoltageRecorderScan, VoltageRecorderScan], scan_files: List[str]
) -> None:
    """Test that aborting the ScanTransfer thread via threading.Condition results in thread termination."""
    (local_scan, remote_scan) = local_remote_scans

    local_scan.update_files()
    remote_scan.update_files()

    cond = threading.Condition()
    scan_transfer = ScanTransfer(local_scan, remote_scan, cond, loop_wait=0.1)
    scan_transfer.start()

    assert scan_transfer.is_alive()

    # wait some time for the ScanTransfer to transfer the data files
    time.sleep(0.5)

    with cond:
        cond.notify()

    # busy wait for the scan to be transferred
    while scan_transfer.is_alive():
        time.sleep(0.1)

    assert scan_transfer.completed is False
    scan_transfer.join()

    # assert the number of remote files is <= local files
    assert len(remote_scan.get_all_files()) <= len(local_scan.get_all_files())
