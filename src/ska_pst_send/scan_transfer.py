# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for transferring files from the PST server to a remote location."""
from __future__ import annotations

import logging
import os
import pathlib
import shutil
import threading
import time
from dataclasses import dataclass, field
from typing import List

from .scan import VoltageRecorderScan

_all__ = [
    "ScanTransfer",
]


@dataclass(order=True)
class PrioritorizedFile:
    """Data class that provides a filename and a transfer prioritory."""

    priority: int
    filename: pathlib.Path = field(compare=False)


class ScanTransfer(threading.Thread):
    """Thread to asynchronously transfer PST data product files to remote storage."""

    def __init__(
        self: ScanTransfer,
        local_scan: VoltageRecorderScan,
        remote_scan: VoltageRecorderScan,
        quit_event: threading.Event,
        logger: logging.Logger | None = None,
    ):
        """Initialise the ScanTransfer object."""
        threading.Thread.__init__(self)

        self.local_scan = local_scan
        self.remote_scan = remote_scan
        self.quit_event = quit_event
        self.logger = logger
        self.continue_transfer = True
        self.logger.debug(f"local={local_scan.data_product_path} remote={remote_scan.data_product_path}")

    def get_untransferred_files(self: ScanTransfer) -> List[PrioritorizedFile]:
        """Return the list of untransferred files for the scan."""
        # update the local and remote scan file lists
        new_local_files = self.local_scan.update_files()
        new_remote_files = self.remote_scan.update_files()
        self.logger.debug(f"found local={new_local_files} and remote={new_remote_files} files")

        local_files = self.local_scan.get_all_files()
        remote_files = self.remote_scan.get_all_files()
        untransferred_files = []

        # self.logger.debug(f"local_files={local_files} remote_files={remote_files}")
        for local in local_files:
            transferred = False
            for remote in remote_files:
                transferred |= (
                    local.file_number == remote.file_number
                    and local.file_size == remote.file_size
                    and local.file_name == remote.file_name
                )

            if not transferred:
                untransferred_files.append(PrioritorizedFile(local.file_number, local.file_name))

        return untransferred_files

    @property
    def keep_transferring(self: ScanTransfer):
        """Return true if the thread should keep transferring."""
        return not self.quit_event.isSet()

    def run(self: ScanTransfer):
        """Run the transfer for the Scan from local to remote."""
        self.logger.debug("starting transfer thread")
        local_path = self.local_scan.data_product_path
        remote_path = self.remote_scan.data_product_path

        while self.keep_transferring:

            untransferred_files = sorted(self.get_untransferred_files())
            for untransferred_file in untransferred_files:

                self.logger.debug(f"untransferred_file={untransferred_file}")
                if not self.keep_transferring:
                    continue

                local_file = local_path / untransferred_file.filename
                remote_file = remote_path / untransferred_file.filename

                self.logger.debug(f"copying {local_file} to {remote_file}")
                os.makedirs(os.path.dirname(remote_file), exist_ok=True)
                shutil.copyfile(local_file, remote_file)

            if self.keep_transferring:
                time.sleep(1)
