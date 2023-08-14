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
from types import TracebackType
from typing import Any, Dict, List, Tuple

import nptyping as npt
import numpy as np

from .scan import VoltageRecorderScan

__all__ = [
    "ScanManager",
]

PST_SUBSYSTEMS = ["pst-low", "pst-mid"]


class ScanManager:
    """
    Class that managers the processing of recorded scans.
    """

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
        for rel_scan_path in self.get_relative_scan_paths():
            matches_existing = [x.match_relative_path(rel_scan_path) for x in self._scans]
            if not any(matches_existing):
                self.logger.debug(f"adding new scan at {str(rel_scan_path)}")
                self._scans.append(VoltageRecorderScan(self.data_product_path, rel_scan_path, self.logger))

        # remove delete scans from the list
        for scan in self._scans:
            matches_existing = [scan.match_relative_path(x) for x in self.get_relative_scan_paths()]
            if not any(matches_existing):
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
        # self.logger.debug(f"scan paths={full_scan_paths}")
        return full_scan_paths

    def get_oldest_scan(self: ScanManager) -> VoltageRecorderScan:
        """Return the oldest scan stored in the data_product_path."""

        # TODO work out oldest scan, for now return first scan in list
        if len(self._scans) > 0:
            return self._scans[0]
        return None

    def generate_stat_files(self: ScanManager, scan: VoltageRecorderScan) -> bool:
        """Generate a stat file for the Scan."""

        (data_file, weights_file) = scan.get_unprocessed_data_weights_files()
        if data_file is None or weights_file is None:
            self.logger.debug("No stats file to generate")
            return

        command = "ska_pst_stat_file_proc -d {data_file} -w {weights_file}"
        proc = subprocess.Popen(
            command,
            cwd=scan.scan_path,
            shell=True,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        try:
            (output, junk) = proc.communicate()
        except IOError as e:
            if e.errno == errno.EINTR:
                self.quit_event.set()
                return (-1, ("SIGINT"))

        # communicate the command
        try:
            (output, junk) = proc.communicate()
        except IOError as e:
            if e.errno == errno.EINTR:
                self.quit_event.set()
                return (-1, ("SIGINT"))

        return_code = proc.returncode
