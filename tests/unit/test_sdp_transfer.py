# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the ScanManager."""
from __future__ import annotations

import logging
import subprocess
import threading
import time
from typing import Any, Tuple, cast
from unittest.mock import MagicMock  # Import the necessary modules

import pytest

from ska_pst_send import ScanProcess, ScanTransfer, SdpTransfer, VoltageRecorderScan


def test_sdp_transfer_process(
    local_remote_scans: Tuple[VoltageRecorderScan, VoltageRecorderScan],
    subsystem_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the process method of SdpTransfer."""
    (local_scan, remote_scan) = local_remote_scans

    local_path = local_scan.data_product_path
    remote_path = remote_scan.data_product_path
    data_product_dasboard = "disabled"
    verbose = False
    sdp_transfer = SdpTransfer(local_path, remote_path, subsystem_id, data_product_dasboard, verbose)

    def _process_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        # ensure the file is created
        for sf in local_scan._stats_files:
            (local_scan.full_scan_path / sf.data_product_path).touch()

        completed = MagicMock()
        completed.returncode = 0
        return completed

    mocked_cmd = MagicMock(side_effect=_process_side_effect)
    monkeypatch.setattr(subprocess, "run", mocked_cmd)

    local_scan._scan_completed_file.touch()
    local_scan._data_product_file.touch()

    def _interrupt_processing() -> None:
        # """Sleep for a timeout, then interrupt SdpTransfer processing."""
        time.sleep(5)
        sdp_transfer.interrrupt_processing()

    notify_thread = threading.Thread(target=_interrupt_processing, daemon=True)
    notify_thread.start()
    sdp_transfer.process()
    notify_thread.join()


def test_metadata_exists_called_with_correct_search_value(
    subsystem_id: str,
    monkeypatch: pytest.MonkeyPatch,
    local_remote_scans: Tuple[VoltageRecorderScan, VoltageRecorderScan],
    logger: logging.Logger,
) -> None:
    """Test metadata exists."""
    (local_scan, remote_scan) = local_remote_scans

    local_path = local_scan.data_product_path
    remote_path = remote_scan.data_product_path
    data_product_dasboard = "http://localhost:8888"
    verbose = False
    sdp_transfer = SdpTransfer(local_path, remote_path, subsystem_id, data_product_dasboard, verbose)
    api_client = MagicMock()
    sdp_transfer._dpd_api_client = api_client

    assert sdp_transfer._dpd_api_client is not None
    monkeypatch.setattr(ScanTransfer, "run", lambda: None)
    monkeypatch.setattr(ScanProcess, "run", lambda: None)

    def _true(self: Any) -> bool:
        return True

    mock_scan_process = MagicMock()
    mock_scan_process.completed = True
    monkeypatch.setattr("ska_pst_send.sdp_transfer.ScanProcess", mock_scan_process)

    mock_scan_transfer = MagicMock()
    mock_scan_transfer.completed = True
    monkeypatch.setattr("ska_pst_send.sdp_transfer.ScanTransfer", mock_scan_transfer)

    expected_search_value = "foobar"
    data_product_file = remote_path / expected_search_value
    logger.info(f"data_product_file={data_product_file}")
    mock_voltage_recorder_scan = MagicMock()
    mock_voltage_recorder_scan.data_product_file_exists.return_value = True
    mock_voltage_recorder_scan.data_product_file = data_product_file
    logger.info(
        f"mock_voltage_recorder_scan.data_product_file={mock_voltage_recorder_scan.data_product_file}"
    )
    monkeypatch.setattr(
        "ska_pst_send.sdp_transfer.VoltageRecorderScan", lambda *args, **kwargs: mock_voltage_recorder_scan
    )

    def _stop_process() -> None:
        import time

        time.sleep(1)
        sdp_transfer.interrrupt_processing()

    t = threading.Thread(target=_stop_process)
    t.start()
    sdp_transfer.process()
    t.join()
    # notify_thread.join()

    cast(MagicMock, api_client.reindex_dataproducts).assert_called_once()
    cast(MagicMock, api_client.metadata_exists).assert_called_once_with(search_value=expected_search_value)

    # Assert that reindex_dataproducts and metadata_exists were called
    sdp_transfer._dpd_api_client.reindex_dataproducts.assert_called_once()
