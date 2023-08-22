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
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialise the ScanProcess object.

        :param VoltageRecorderScan scan: voltage recorder scan to be processed by the run method.
        :param threading.Condition exit_cond: condition variable to use to trigger thread termination.
        :param logging.Logger logger: The logger instance to use.
        :param int loop_wait: timeout for the main processing loop.
        """
        threading.Thread.__init__(self, daemon=True)

        self.scan = scan
        self.exit_cond = exit_cond
        self.logger = logger or logging.getLogger(__name__)
        self.loop_wait = loop_wait
        self.completed = False

    def run(self: ScanProcess) -> None:
        """Perform processing of scan files."""
        self.logger.debug("starting scan processing thread")

        while not self.completed:

            # get an unprocessed file
            unprocessed_file = self.scan.next_unprocessed_file
            if unprocessed_file is None:
                if self.scan.is_complete:
                    if not self.scan.data_product_file_exists:
                        self.logger.debug("generating data product YAML file")
                        self.scan.generate_data_product_file()
                    self.completed = True
            else:
                self.logger.debug(f"processing {unprocessed_file}")
                result = self.scan.process_file(unprocessed_file)  # type: ignore
                self.logger.debug(f"result={result}")

            if not self.completed:
                with self.exit_cond:
                    if self.exit_cond.wait(timeout=self.loop_wait):
                        self.logger.debug("ScanProcess thread exiting on command")
                        return

        self.logger.debug("ScanProcess thread exiting as processing is complete")
