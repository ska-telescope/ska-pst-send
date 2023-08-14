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
import time
from typing import Any

from .scan import VoltageRecorderScan

_all__ = [
    "ScanProcess",
]


class ScanProcess(threading.Thread):
    """Thread to asynchronously generate PST data product files for transfer to remote storage."""

    def __init__(
        self: ScanProcess,
        scan: VoltageRecorderScan,
        quit_event: threading.Event,
        logger: logging.Logger | None = None,
    ):
        """Initialise the ScanProcess object."""
        threading.Thread.__init__(self)

        self.scan = scan
        self.quit_event = quit_event
        self.logger = logger

    def get_unprocessed_file(self: ScanProcess) -> Any | None:
        """Get a Scan dependent object (e.g. a Tuple) of an unprocessed file or None."""
        return self.scan.get_unprocessed_file()

    @property
    def keep_processing(self: ScanProcess) -> bool:
        """Return true if the thread should keep processing."""
        return not self.quit_event.isSet()

    def run(self: ScanProcess):
        """Perform processing of scan files."""
        self.logger.debug("starting processing thread")
        fully_processed = False
        while self.keep_processing and not fully_processed:

            unprocessed_file = self.get_unprocessed_file()
            if unprocessed_file == (None, None, None):
                if self.scan.scan_completed_exists:
                    if not self.scan.data_product_file_exists:
                        self.logger.debug("generating data product YAML file")
                        self.generate_data_product_file()
                    self.logger.debug("ceasing processing")
                    fully_processed = True
            else:
                self.logger.debug(f"processing file {unprocessed_file}")
                result = self.scan.process_file(unprocessed_file)
                self.logger.debug(f"result={result}")

            if self.keep_processing:
                time.sleep(1)
