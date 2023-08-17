# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the scans."""

import pathlib
from typing import List

import pytest

from ska_pst_send import VoltageRecorderFile, VoltageRecorderScan


def test_constructor(voltage_recording_scan: VoltageRecorderScan, scan_files) -> None:

    scan = voltage_recording_scan
    assert scan.scan_config_file_exists
    assert scan.is_scan_recording == True
    assert scan.data_product_file_exists == False
    assert scan.is_scan_completed == False

    # assert the scan is constructed with the correect number of files
    assert len(scan.get_all_files()) == len(scan_files) + 1


def test_update_files(voltage_recording_scan: VoltageRecorderScan, scan_files: List[str]) -> None:

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
    assert scan.is_scan_recording == False
    assert scan.is_scan_completed

    # the scan completed file is not a new file to be transferred
    scan.update_files()
    assert len(scan.get_all_files()) == len(scan_files) + 2


def test_get_unprocessed_file(
    voltage_recording_scan: VoltageRecorderScan,
    data_files: List[str],
    weights_files: List[str],
    stats_files: List[str],
) -> None:

    scan = voltage_recording_scan

    # process each of the four data files, noting this will only work whilst the processor is "touch"
    for i in range(len(data_files)):
        unprocessed_file = scan.get_unprocessed_file()
        expected = (
            VoltageRecorderFile(scan.full_scan_path / data_files[i], scan.data_product_path),
            VoltageRecorderFile(scan.full_scan_path / weights_files[i], scan.data_product_path),
            VoltageRecorderFile(scan.full_scan_path / stats_files[i], scan.data_product_path),
        )
        assert unprocessed_file[0] == expected[0]
        assert unprocessed_file[1] == expected[1]

        result = scan.process_file(unprocessed_file)
        assert result
        assert unprocessed_file[2].exists
        assert unprocessed_file[2] == expected[2]

    unprocessed_file = scan.get_unprocessed_file()
    assert unprocessed_file == (None, None, None)
