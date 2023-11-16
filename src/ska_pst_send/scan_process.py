# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for asynchronously processing Scan data products into output data products."""
from __future__ import annotations

import logging
import threading

from .voltage_recorder_scan import VoltageRecorderScan

_all__ = [
    "ScanProcess",
]


class ScanProcess(threading.Thread):
    """Thread to asynchronously generate PST data product files for transfer to remote storage."""

    def __init__(
        self: ScanProcess,
        scan: VoltageRecorderScan,
        exit_cond: threading.Condition,
        loop_wait: float = 2,
        minimum_age: float = 10,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialise the ScanProcess object.

        :param scan: voltage recorder scan to be processed by the run method.
        :param exit_cond: condition variable to use to trigger thread termination.
        :param loop_wait: timeout for the main processing loop.
        :param minimum_age: minimum age to require for unprocessed files, in seconds.
        :param logger: the logger instance to use.
        """
        threading.Thread.__init__(self, daemon=True)

        self.scan = scan
        self.exit_cond = exit_cond
        self.logger = logger or logging.getLogger(__name__)
        self.loop_wait = loop_wait
        self.minimum_age = minimum_age
        self.completed = False

    def _handle_scan_potentially_complete(self: ScanProcess) -> None:
        self.logger.debug(f"checking if scan {self.scan.scan_id} is actually complete.")
        if self.scan.is_complete() and self.scan.next_unprocessed_file(minimum_age=0) is None:
            self.logger.debug(
                f"scan {self.scan.scan_id} has all files processed and has received scan_complete file"
            )
            self.logger.debug(f"generating data product YAML file for scan {self.scan.scan_id}")
            self.scan.generate_data_product_file()
            # only mark as completed after generating data product file
            self.completed = True

    def run(self: ScanProcess) -> None:
        """Perform processing of scan files."""
        self.logger.debug(f"{self} starting scan processing thread")

        try:
            while not self.completed and self.scan.is_valid():
                self.scan.process_next_unprocessed_file(minimum_age=self.minimum_age)
                self._handle_scan_potentially_complete()

                # if not yet completed, conditional wait on exit condition variable
                if not self.completed:
                    with self.exit_cond:
                        if self.exit_cond.wait(timeout=self.loop_wait):
                            self.logger.debug("ScanProcess thread exiting on command")
                            return

            if self.completed:
                self.logger.info(f"{self} thread exiting as processing is complete")
            elif self.scan.transfer_failed:
                self.logger.info(f"{self} thread exiting due to the transfer thread failing")
            elif not self.scan.path_exists():
                self.logger.info(f"{self} thread exiting due to scan directory no exists")
        except Exception:
            self.logger.exception(f"{self} thread received an exception. Exiting loop.", exc_info=True)
            self.scan.processing_failed = True

    def __repr__(self: ScanProcess) -> str:
        """Get string representation for scan process."""
        return f"ScanProcess(scan_id={self.scan.scan_id})"
