# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for transferring files from the PST server to a remote location."""
from __future__ import annotations

import logging
import shutil
import threading
from typing import List

from .voltage_recorder_file import VoltageRecorderFile
from .voltage_recorder_scan import VoltageRecorderScan

_all__ = [
    "ScanTransfer",
]


class ScanTransfer(threading.Thread):
    """Thread to asynchronously transfer PST data product files to remote storage."""

    def __init__(
        self: ScanTransfer,
        local_scan: VoltageRecorderScan,
        remote_scan: VoltageRecorderScan,
        exit_cond: threading.Condition,
        logger: logging.Logger | None = None,
    ):
        """Initialise the ScanTransfer object."""
        threading.Thread.__init__(self)

        self.local_scan = local_scan
        self.remote_scan = remote_scan
        self.exit_cond = exit_cond
        self.logger = logger or logging.getLogger(__name__)
        self.completed = False
        self.loop_wait = 2
        self.logger.debug(f"local={local_scan.data_product_path} remote={remote_scan.data_product_path}")

    def get_untransferred_files(self: ScanTransfer) -> List[VoltageRecorderFile]:
        """Return the list of untransferred files for the scan."""
        # update the local and remote scan file lists
        self.local_scan.update_files()
        self.remote_scan.update_files()

        local_files = self.local_scan.get_all_files()
        remote_files = self.remote_scan.get_all_files()
        self.logger.debug(f"local_files count={len(local_files)}")
        self.logger.debug(f"remote_files count={len(remote_files)}")

        # build the list of untransferred files
        untransferred_files = [local for local in local_files if local not in remote_files]
        self.logger.debug(f"untransferred_files count={len(untransferred_files)}")

        return untransferred_files

    def run(self: ScanTransfer):
        """Run the transfer for the Scan from local to remote."""
        self.logger.debug("starting transfer thread")
        local_path = self.local_scan.data_product_path
        remote_path = self.remote_scan.data_product_path

        while not self.completed:

            untransferred_files = sorted(self.get_untransferred_files())
            for untransferred_file in untransferred_files:
                self.logger.debug(f"untransferred_file={untransferred_file}")

                # check for the exit condition, with a small timeout
                with self.exit_cond:
                    if self.exit_cond.wait(timeout=0.1):
                        self.logger.debug("ScanTransfer thread exiting on command")
                        return

                local_file = local_path / untransferred_file.relative_path
                remote_file = remote_path / untransferred_file.relative_path
                self.logger.info(f"copying {untransferred_file.relative_path} to {remote_file}")
                remote_file.parent.mkdir(mode=0o644, parents=True, exist_ok=True)
                shutil.copyfile(local_file, remote_file)

            # check if the scan is completed and the ScanProcess has generated the data-product-file
            if (
                len(untransferred_files) == 0
                and self.local_scan.is_scan_completed
                and self.local_scan.data_product_file_exists
            ):
                self.completed = True
            else:
                with self.exit_cond:
                    if self.exit_cond.wait(timeout=self.loop_wait):
                        self.logger.debug("ScanTransfer thread exiting on command")
                        return

        self.logger.debug("ScanTransfer thread exiting as transfer complete")
