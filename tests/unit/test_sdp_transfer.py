# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the ScanManager."""
from __future__ import annotations

import threading
import time

from ska_pst_send import SdpTransfer, VoltageRecorderScan


def test_sdp_transfer_process(
    local_remote_scans: (VoltageRecorderScan, VoltageRecorderScan), subsystem_id: str
) -> None:
    """Test the process method of SdpTransfer."""
    (local_scan, remote_scan) = local_remote_scans

    local_path = local_scan.data_product_path
    remote_path = remote_scan.data_product_path
    data_product_dasboard = "disabled"
    verbose = False
    sdp_transfer = SdpTransfer(local_path, remote_path, subsystem_id, data_product_dasboard, verbose)

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
