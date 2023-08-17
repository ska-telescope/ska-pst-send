# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for managing scans of recorded by the PST AA0.5 Voltage Recorder."""
from __future__ import annotations

import logging
import os
import pathlib
from typing import List

from .voltage_recorder_scan import VoltageRecorderScan

__all__ = [
    "ScanManager",
]

PST_SUBSYSTEMS = ["pst-low", "pst-mid"]


class ScanManager:
    """Class that managers the processing of recorded scans."""

    def __init__(
        self: ScanManager,
        data_product_path: pathlib.Path,
        subsystem: str,
        logger: logging.Logger | None = None,
    ) -> None:
        """Init object.

        param data_product_path: The absolute path containing scans
        param subsystem: The PST instance
        """
        assert data_product_path.exists() and data_product_path.is_dir()
        assert subsystem in PST_SUBSYSTEMS

        self.data_product_path = data_product_path
        self.subsystem = subsystem
        self._scans = []
        self.logger = logger or logging.getLogger(__name__)

        # initialise the list of scans
        self.refresh_scans()

    def refresh_scans(self: ScanManager):
        """Update the list of scans."""
        # add new scans to the list
        all_scan_rel_paths = [rp for s in self._scans for rp in s.relative_scan_path]
        for rel_scan_path in self.get_relative_scan_paths():
            if rel_scan_path not in all_scan_rel_paths:
                self.logger.debug(f"adding new scan {rel_scan_path}")
                self._scans.append(VoltageRecorderScan(self.data_product_path, rel_scan_path, self.logger))

        # remove delete scans from the list
        for scan in self._scans:
            if scan.relative_scan_path not in self.get_relative_scan_paths():
                self.logger.debug(f"removing scan at {str(rel_scan_path)}")
                self._scans.remove(scan)

    def get_relative_scan_paths(self: ScanManager) -> List[pathlib.Path]:
        """Return a of the relative scan paths stored in the data_product_path."""
        full_scan_paths = self.get_scan_paths()
        relative_scan_paths = [os.path.relpath(x, self.data_product_path) for x in full_scan_paths]
        return relative_scan_paths

    def get_scan_paths(self: ScanManager) -> List[pathlib.Path]:
        """Return a list of scans stored in the data_product_path."""
        full_scan_paths = list(self.data_product_path.glob(f"*/{self.subsystem}/*"))
        return full_scan_paths

    def get_oldest_scan(self: ScanManager) -> VoltageRecorderScan:
        """Return the oldest scan stored in the data_product_path."""
        self.refresh_scans()

        # TODO work out oldest scan, for now return first scan in list
        if len(self._scans) > 0:
            return self._scans[0]
        return None
