# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for managing scans of recorded by the PST AA0.5 Voltage Recorder."""
from __future__ import annotations

import logging
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
        """Initialise a ScanManager object.

        :param pathlib data_product_path: absolute file system path to the data product directory
        :param str subsystem: The PST instance, one of pst-low or pst-mid
        :param logging.Logger logger: The logger instance to use.
        """
        assert data_product_path.exists() and data_product_path.is_dir()
        assert subsystem in PST_SUBSYSTEMS

        self.data_product_path = data_product_path
        self.subsystem = subsystem
        self._scans: List[VoltageRecorderScan] = []
        self.logger = logger or logging.getLogger(__name__)

        # initialise the list of scans
        self._refresh_scans()

    def _refresh_scans(self: ScanManager) -> None:
        """Update the list of scans."""
        # add new scans to the list
        all_scan_rel_paths = [s.relative_scan_path for s in self._scans]
        for rel_scan_path in self.relative_scan_paths:
            if rel_scan_path not in all_scan_rel_paths:
                self.logger.debug(f"adding new scan {rel_scan_path}")
                self._scans.append(VoltageRecorderScan(self.data_product_path, rel_scan_path, self.logger))

        # remove delete scans from the list
        for scan in self._scans:
            if scan.relative_scan_path not in self.relative_scan_paths:
                self.logger.debug(f"removing scan at {str(scan.relative_scan_path)}")
                self._scans.remove(scan)

    @property
    def relative_scan_paths(self: ScanManager) -> List[pathlib.Path]:
        """
        Return a current list of the relative scan paths stored in the data_product_path.

        :return: the list of relative scan paths.
        :rtype: List[pathlib.Path].
        """
        return [x.relative_to(self.data_product_path) for x in self.scan_paths]

    @property
    def scan_paths(self: ScanManager) -> List[pathlib.Path]:
        """
        Return a list of the current full scan paths stored in the data_product_path.

        :return: the list of full scan paths.
        :rtype: List[pathlib.Path].
        """
        return list(self.data_product_path.glob(f"*/{self.subsystem}/*"))

    @property
    def oldest_scan(self: ScanManager) -> VoltageRecorderScan | None:
        """
        Return the oldest scan stored in the data_product_path.

        :return: the older scan currently stored in the data product path, or None if empty
        :rtype: VoltageRecorderScan | None
        """
        self._refresh_scans()

        # TODO work out oldest scan, for now return first scan in list
        if len(self._scans) > 0:
            return self._scans[0]
        return None
