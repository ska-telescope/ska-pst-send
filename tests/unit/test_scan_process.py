# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the scan process thread."""

import subprocess
import threading
import time
from typing import Any, List
from unittest.mock import MagicMock

import pytest

import ska_pst_send.voltage_recorder_scan
from ska_pst_send import ScanProcess, VoltageRecorderFile, VoltageRecorderScan


def test_constructor(voltage_recording_scan: VoltageRecorderScan, scan_files: List[str]) -> None:
    """Test the ScanProcess constructor initialises the object as required."""
    scan = voltage_recording_scan

    cond = threading.Condition()
    scan_process = ScanProcess(scan, cond)
    assert scan_process.completed is False
    assert scan_process.is_alive() is False
    assert len(scan.get_all_files()) == len(scan_files) + 1


def test_process(
    voltage_recording_scan: VoltageRecorderScan,
    data_files: List[str],
    weights_files: List[str],
    stats_files: List[str],
    scan_files: List[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the ScanProcess can fully process a completed scan."""
    scan = voltage_recording_scan
    assert len(scan.get_all_files()) == len(scan_files) + 1

    mock_metadata_builder = MagicMock()
    monkeypatch.setattr(ska_pst_send.voltage_recorder_scan, "MetaDataBuilder", mock_metadata_builder)

    def _process_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        # ensure the file is created
        for sf in stats_files:
            full_sf = scan.full_scan_path / sf
            full_sf.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
            full_sf.touch()

        completed = MagicMock()
        completed.returncode = 0
        return completed

    mocked_cmd = MagicMock(side_effect=_process_side_effect)
    monkeypatch.setattr(subprocess, "run", mocked_cmd)

    cond = threading.Condition()
    scan_process = ScanProcess(scan, cond, loop_wait=0.1, minimum_age=0)

    # Assert that there are unprocessed files
    expected = (
        VoltageRecorderFile(scan.full_scan_path / data_files[0], scan.data_product_path),
        VoltageRecorderFile(scan.full_scan_path / weights_files[0], scan.data_product_path),
        VoltageRecorderFile(scan.full_scan_path / stats_files[0], scan.data_product_path),
    )
    assert scan.next_unprocessed_file(minimum_age=0) == expected

    # start the ScanProcess thread
    scan_process.start()
    assert scan_process.is_alive()

    # wait some time for the ScanProcess to process the data files
    time.sleep(0.5)

    # assert there are no more unprocessed files
    assert scan.next_unprocessed_file(minimum_age=0) is None

    # assert that the scan is still incomplete since the data_product file and scan_completed
    # file do not yet exist
    assert scan_process.completed is False

    # touch the remaining files
    scan._data_product_file.touch()
    scan._scan_completed_file.touch()

    # wait some time for the ScanProcess to process the data files
    while scan_process.is_alive():
        time.sleep(0.1)

    # assert that the Scan Process thread exited naturally
    assert scan_process.completed
    scan_process.join()

    # assert that each expected stat file exists with the expected name
    for stat_file in stats_files:
        stat_file_path = scan.full_scan_path / stat_file
        assert stat_file_path.exists()


def test_abort_process(
    voltage_recording_scan: VoltageRecorderScan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the ScanProcess thread can be aborted via the threading.Condition variable."""
    scan = voltage_recording_scan
    assert not scan.transfer_failed, "expected scan's transfer_failed to be False"
    assert not scan.processing_failed, "expected scan's processing_failed to be False"
    cond = threading.Condition()

    def _process_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        # ensure the file is created
        completed = MagicMock()
        completed.returncode = 0
        return completed

    mocked_cmd = MagicMock(side_effect=_process_side_effect)
    monkeypatch.setattr(subprocess, "run", mocked_cmd)

    scan_process = ScanProcess(scan, cond, loop_wait=0.1)
    scan_process.start()
    assert scan_process.is_alive()

    time.sleep(scan_process.loop_wait)

    with cond:
        cond.notify()

    # wait for 2 x loop_wait for the process to exit
    time.sleep(scan_process.loop_wait)
    scan_process.join()

    assert scan_process.is_alive() is False
    assert scan_process.completed is False
    assert not scan.transfer_failed, "expected scan's transfer_failed to be False"
    assert not scan.processing_failed, "expected scan's processing_failed to be False"


def test_run_exits_if_transfer_fails(
    voltage_recording_scan: VoltageRecorderScan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that ScanProcess.run exits if the scan transfer fails."""
    scan = voltage_recording_scan
    assert not scan.transfer_failed, "expected scan's transfer_failed to be False"
    assert not scan.processing_failed, "expected scan's processing_failed to be False"
    cond = threading.Condition()

    def _process_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        # ensure the file is created
        completed = MagicMock()
        completed.returncode = 0
        return completed

    mocked_cmd = MagicMock(side_effect=_process_side_effect)
    monkeypatch.setattr(subprocess, "run", mocked_cmd)

    scan_process = ScanProcess(scan, cond, loop_wait=0.1)
    scan_process.start()
    assert scan_process.is_alive()

    time.sleep(0.1)
    scan.transfer_failed = True

    # wait for 2 x loop_wait for the process to exit
    time.sleep(scan_process.loop_wait)
    scan_process.join()

    assert scan_process.is_alive() is False
    assert scan_process.completed is False
    assert scan.transfer_failed, "expected scan's transfer_failed to be True"
    assert not scan.processing_failed, "expected scan's processing_failed to be False"


def test_run_exits_if_exception_thrown(
    voltage_recording_scan: VoltageRecorderScan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that ScanProcess.run exits if the scan transfer fails."""
    scan = voltage_recording_scan
    assert not scan.transfer_failed, "expected scan's transfer_failed to be False"
    assert not scan.processing_failed, "expected scan's processing_failed to be False"
    cond = threading.Condition()

    def _process_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        # ensure the file is created
        raise Exception("process error")

    mocked_cmd = MagicMock(side_effect=_process_side_effect)
    monkeypatch.setattr(voltage_recording_scan, "process_next_unprocessed_file", mocked_cmd)

    scan_process = ScanProcess(scan, cond, loop_wait=0.1)
    scan_process.start()

    scan_process.join()

    assert scan_process.is_alive() is False
    assert scan_process.completed is False
    assert not scan.transfer_failed, "expected scan's transfer_failed to be False"
    assert scan.processing_failed, "expected scan's processing_failed to be True"
