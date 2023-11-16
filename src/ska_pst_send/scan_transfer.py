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
        loop_wait: float = 2,
        dir_perms: int = 0o777,
        minimum_age: float = 10,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialise the ScanTransfer object.

        :param local_scan: scan to be transferred to the remote.
        :param remote_scan: scan to which the local scan will be transferred.
        :param exit_cond: condition variable to use to trigger thread termination.
        :param loop_wait: timeout for the main processing loop.
        :param dir_perms: octal permissions to apply when creating directories during transfer.
        :param minimum_age: minimum age to require for untransferred files, in seconds.
        :param logger: the logger instance to use.
        """
        threading.Thread.__init__(self, daemon=True)

        self.local_scan = local_scan
        self.remote_scan = remote_scan
        self.exit_cond = exit_cond
        self.logger = logger or logging.getLogger(__name__)
        self.loop_wait = loop_wait
        self.default_dir_perms = dir_perms
        self.minimum_age = minimum_age
        self.completed = False
        self.logger.debug(f"local={local_scan.data_product_path} remote={remote_scan.data_product_path}")

    def untransferred_files(self: ScanTransfer, minimum_age: float) -> List[VoltageRecorderFile]:
        """
        Return the list of untransferred files for the scan.

        :param minimum_age: minimum file age to use when returning untransferred files
        :return: the list of voltage recorder files
        :rtype: List[VoltageRecorderFile].
        """
        # update the local and remote scan file lists
        self.local_scan.update_files()
        self.remote_scan.update_files()

        local_files = self.local_scan.get_all_files()
        remote_files = self.remote_scan.get_all_files()
        self.logger.debug(f"local_files count={len(local_files)}")
        self.logger.debug(f"remote_files count={len(remote_files)}")

        # build the list of untransferred files
        files = [local for local in local_files if local not in remote_files and local.age >= minimum_age]
        self.logger.debug(f"files count={len(files)}")

        return sorted(files)

    def _transfer_files(self: ScanTransfer) -> bool:
        local_path = self.local_scan.data_product_path
        remote_path = self.remote_scan.data_product_path

        for untransferred_file in self.untransferred_files(self.minimum_age):
            self.logger.debug(f"untransferred_file={untransferred_file} with age > {self.minimum_age}")

            # check for the exit condition, with a small timeout
            with self.exit_cond:
                if self.exit_cond.wait(timeout=0.1):
                    self.logger.debug("ScanTransfer thread exiting on command")
                    return False

            local_file = local_path / untransferred_file.relative_path
            remote_file = remote_path / untransferred_file.relative_path
            self.logger.info(f"transferring {untransferred_file.relative_path}")
            remote_file.parent.mkdir(mode=self.default_dir_perms, parents=True, exist_ok=True)
            shutil.copyfile(local_file, remote_file)
            self.logger.debug(f"{untransferred_file.relative_path} has been transferred")
            self.local_scan.update_modified_time()

        # check if the scan is completed and the ScanProcess has generated the data-product-file
        self.completed = (
            len(self.untransferred_files(minimum_age=0)) == 0
            and self.local_scan.is_complete()
            and self.local_scan.data_product_file_exists()
        )

        return True

    def run(self: ScanTransfer) -> None:
        """Run the transfer for the Scan from local to remote."""
        self.logger.debug(f"{self} starting transfer thread")

        try:
            while not self.completed and self.local_scan.is_valid():
                # if received exit condition during loop exit out.
                if not self._transfer_files():
                    return

                # if not yet completed, timeout wait on the exit condition
                if not self.completed:
                    with self.exit_cond:
                        if self.exit_cond.wait(timeout=self.loop_wait):
                            self.logger.debug("ScanTransfer thread exiting on command")
                            return

            if self.completed:
                self.logger.info(f"{self} thread exiting as transfer is complete")
            elif self.local_scan.processing_failed:
                self.logger.info(f"{self} thread exiting due to the processing thread failing")
            elif not self.local_scan.path_exists():
                self.logger.info(f"{self} thread exiting due to scan directory no exists")
        except Exception:
            self.logger.exception(f"{self} thread received an exception. Exiting loop.", exc_info=True)
            self.local_scan.transfer_failed = True

    def __repr__(self: ScanTransfer) -> str:
        """Get string representation for scan transfer thread."""
        return f"ScanTransfer(scan_id={self.local_scan.scan_id})"
