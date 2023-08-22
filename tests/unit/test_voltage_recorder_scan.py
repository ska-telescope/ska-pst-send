# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the scans."""

import pathlib
import subprocess
from typing import Any, List
from unittest.mock import MagicMock

import pytest

from ska_pst_send import VoltageRecorderFile, VoltageRecorderScan
from tests.conftest import create_voltage_recorder_scan, remove_send_tempdir


def test_constructor(local_product_path: pathlib.Path, scan_path: pathlib.Path) -> None:
    """Test the VoltageRecorderScan constructor."""
    try:
        scan = create_voltage_recorder_scan(local_product_path, scan_path)
        assert scan.scan_config_file_exists is False
        assert scan.is_recording
        assert scan.data_product_file_exists is False
        assert scan.is_complete is False
        assert len(scan.get_all_files()) == 0
    finally:
        remove_send_tempdir()


def test_update_files(voltage_recording_scan: VoltageRecorderScan, scan_files: List[str]) -> None:
    """Test the udpate_files method of VoltageRecorderScan."""
    scan = voltage_recording_scan

    # check the file count matches the expected: scan_files + scan_config
    assert len(scan.get_all_files()) == len(scan_files) + 1

    # manually create the ska-data-product.yaml file
    scan._data_product_file.touch()
    assert scan.data_product_file_exists

    # check the file count matches the expected: scan_files + scan_config + data_product
    assert len(scan.get_all_files()) == len(scan_files) + 2

    # manually create the scan_completed file
    scan._scan_completed_file.touch()
    assert scan.is_recording is False
    assert scan.is_complete

    # ensure the scan_complete file is not counted:
    # i.e. check the file count matches the expected: scan_files + scan_config + data_product
    scan.update_files()
    assert len(scan.get_all_files()) == len(scan_files) + 2


def test_next_unprocessed_file(
    voltage_recording_scan: VoltageRecorderScan,
    data_files: List[str],
    weights_files: List[str],
    stats_files: List[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the next_unprocessed_file property of VoltageRecorderScan."""
    mocked_command = MagicMock()
    monkeypatch.setattr(subprocess, "run", mocked_command)

    scan = voltage_recording_scan

    sorted_data_files = sorted(data_files)
    sorted_weights_files = sorted(weights_files)
    sorted_stats_files = sorted(stats_files)

    # process each of the four data files, noting this will only work whilst the processor is "touch"
    for (i, df) in enumerate(data_files):
        unprocessed_file = scan.next_unprocessed_file
        assert unprocessed_file is not None, f"Expected that there should be an unprocessed file for {df}"
        expected = (
            VoltageRecorderFile(scan.full_scan_path / sorted_data_files[i], scan.data_product_path),
            VoltageRecorderFile(scan.full_scan_path / sorted_weights_files[i], scan.data_product_path),
            VoltageRecorderFile(scan.full_scan_path / sorted_stats_files[i], scan.data_product_path),
        )
        assert unprocessed_file[0] == expected[0]
        assert unprocessed_file[1] == expected[1]

        def _process_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
            file: pathlib.Path = unprocessed_file[2].file_name
            if file.exists():
                file.unlink()
            file.touch()

            completed = MagicMock()
            completed.returncode = 0

            return completed

        mocked_command.side_effect = _process_side_effect

        assert scan.process_file(unprocessed_file)

        expected_cmd = [
            "ska_pst_stat_file_proc",
            "-d",
            str(unprocessed_file[0]),
            "-w",
            str(unprocessed_file[1]),
        ]

        mocked_command.assert_called_once_with(
            expected_cmd,
            cwd=scan.full_scan_path,
            shell=False,
            stdin=None,
            capture_output=True,
        )

        mocked_command.reset_mock()

        assert unprocessed_file[2].exists
        assert unprocessed_file[2] == expected[2]

    assert scan.next_unprocessed_file is None
