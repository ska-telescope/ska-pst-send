# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the scans."""

import pathlib
from typing import List

from ska_pst_send import VoltageRecorderFile, VoltageRecorderScan
from tests.conftest import create_voltage_recorder_scan, remove_product


def test_constructor(local_product_path: pathlib.Path, scan_path: pathlib) -> None:
    """Test the VoltageRecorderScan constructor."""
    try:
        scan = create_voltage_recorder_scan(local_product_path, scan_path)
        assert scan.scan_config_file_exists is False
        assert scan.is_recording
        assert scan.data_product_file_exists is False
        assert scan.is_complete is False
        assert len(scan.get_all_files()) == 0
    except Exception as exc:
        print(exc)
        assert False
    finally:
        remove_product(local_product_path)


def test_update_files(voltage_recording_scan: VoltageRecorderScan, scan_files: List[str]) -> None:
    """Test the udpate_files method of VoltageRecorderScan."""
    scan = voltage_recording_scan

    # check the file count matches the expected values
    assert len(scan.get_all_files()) == len(scan_files) + 1

    # manually create the ska-data-product.yaml file
    scan._data_product_file.touch()
    assert scan.data_product_file_exists

    # ensure this file is detected in the file list
    assert len(scan.get_all_files()) == len(scan_files) + 2

    # manually create the scan_completed file
    scan._scan_completed_file.touch()
    assert scan.is_recording is False
    assert scan.is_complete

    # the scan completed file is not a new file to be transferred
    scan.update_files()
    assert len(scan.get_all_files()) == len(scan_files) + 2


def test_next_unprocessed_file(
    voltage_recording_scan: VoltageRecorderScan,
    data_files: List[str],
    weights_files: List[str],
    stats_files: List[str],
) -> None:
    """Test the next_unprocessed_file property of VoltageRecorderScan."""
    scan = voltage_recording_scan

    sorted_data_files = sorted(data_files)
    sorted_weights_files = sorted(weights_files)
    sorted_stats_files = sorted(stats_files)

    # process each of the four data files, noting this will only work whilst the processor is "touch"
    for i in range(len(data_files)):
        unprocessed_file = scan.next_unprocessed_file
        expected = (
            VoltageRecorderFile(scan.full_scan_path / sorted_data_files[i], scan.data_product_path),
            VoltageRecorderFile(scan.full_scan_path / sorted_weights_files[i], scan.data_product_path),
            VoltageRecorderFile(scan.full_scan_path / sorted_stats_files[i], scan.data_product_path),
        )
        assert unprocessed_file[0] == expected[0]
        assert unprocessed_file[1] == expected[1]

        assert scan.process_file(unprocessed_file)
        assert unprocessed_file[2].exists
        assert unprocessed_file[2] == expected[2]

    assert scan.next_unprocessed_file == (None, None, None)
