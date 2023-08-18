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


class NotifyThread(threading.Thread):
    """Background thread to notify the SdpTransfer class to exit after a timeout."""

    def __init__(self: NotifyThread, sdp_transfer: SdpTransfer, timeout: int) -> None:
        """Construct the NotifyThread object."""
        threading.Thread.__init__(self, daemon=True)
        self.sdp_transfer = sdp_transfer
        self.timeout = timeout

    def run(self: NotifyThread) -> None:
        """Run the notify thread."""
        time.sleep(self.timeout)
        self.sdp_transfer.persist = False
        with self.sdp_transfer.cond:
            self.sdp_transfer.cond.notify_all()


def test_sdp_transfer_process(
    local_remote_scans: (VoltageRecorderScan, VoltageRecorderScan), ss_id: str
) -> None:
    """Test the process method of SdpTransfer."""
    (local_scan, remote_scan) = local_remote_scans

    local_path = local_scan.data_product_path
    remote_path = remote_scan.data_product_path
    data_product_dasboard = "disabled"
    verbose = False
    sdp_transfer = SdpTransfer(local_path, remote_path, ss_id, data_product_dasboard, verbose)

    local_scan._scan_completed_file.touch()
    local_scan._data_product_file.touch()

    notify_thread = NotifyThread(sdp_transfer, 5)
    notify_thread.start()
    sdp_transfer.process()
    notify_thread.join()
