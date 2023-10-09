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
        if not self.scan.next_unprocessed_file(minimum_age=self.minimum_age):
            self.logger.debug("generating data product YAML file")
            self.scan.generate_data_product_file()
            # only mark as completed after generating data product file
            self.completed = True

    def run(self: ScanProcess) -> None:
        """Perform processing of scan files."""
        self.logger.debug("starting scan processing thread")

        try:
            while not self.completed:
                self.scan.process_next_unprocessed_file(minimum_age=self.minimum_age)

                if self.scan.is_complete():
                    self._handle_scan_potentially_complete()

                # if not yet completed, conditional wait on exit condition variable
                if not self.completed:
                    with self.exit_cond:
                        if self.exit_cond.wait(timeout=self.loop_wait):
                            self.logger.debug("ScanProcess thread exiting on command")
                            return

            self.logger.info(
                f"ScanProcess thread exiting as processing for scan {self.scan.scan_id} complete"
            )
        except Exception:
            self.logger.exception("ScanProcess loop received an exception. Exiting loop.", exc_info=True)
