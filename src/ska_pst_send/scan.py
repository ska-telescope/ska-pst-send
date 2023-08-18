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
import shutil

__all__ = [
    "Scan",
]


class Scan:
    """Base class for representing PST Scan Data Products, stored on the local file system."""

    def __init__(
        self: Scan,
        data_product_path: pathlib.Path,
        relative_scan_path: pathlib.Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Init object.

        param data_product_path: The path of the data product directory containing the scan
        param scan_path: The full path for the scan within the scan
        """
        self.data_product_path = data_product_path
        self.relative_scan_path = relative_scan_path
        self.full_scan_path = data_product_path / relative_scan_path
        self.logger = logger or logging.getLogger(__name__)

        assert self.data_product_path.exists() and self.data_product_path.is_dir()

        self._scan_config_file = self.full_scan_path / "scan_configuration.json"
        self._data_product_file = self.full_scan_path / "ska-data-product.yaml"
        self._scan_completed_file = self.full_scan_path / "scan_completed"

    def delete_scan(self: Scan) -> None:
        """Delete all the local data files associated with a scan."""
        self.logger.debug(f"deleting all {self.relative_scan_path}")
        # first delete all files in the scan directory
        shutil.rmtree(self.full_scan_path)

        # then move up the directory tree to the data_product path, pruning directory if empty
        to_prune = self.full_scan_path.parent
        can_prune = True
        while can_prune:
            try:
                delta = to_prune.relative_to(self.data_product_path)
                if delta == pathlib.Path("."):
                    self.logger.debug("pruned scan_path: stopping prune")
                    can_prune = False
                    continue
                try:
                    # remove the directory, if it is empty
                    to_prune.rmdir()
                    to_prune = to_prune.parent
                except OSError as exc:
                    self.logger.debug(f"found non-empty parent directory, stopping prune: {exc}")
                    can_prune = False
            except ValueError as exc:
                self.logger.debug(f"walked above data_product_path, stopping prune: {exc}")
                can_prune = False

    @property
    def is_recording(self: Scan) -> bool:
        """Return true is the scan been not yet been marked as completed."""
        return not self._scan_completed_file.exists()

    @property
    def data_product_file_exists(self: Scan) -> bool:
        """Return true if the ska-pst-dataproduct.yaml file exists."""
        return self._data_product_file.exists()

    @property
    def scan_config_file_exists(self: Scan) -> bool:
        """Return true if the scan-config.json file exists."""
        return self._scan_config_file.exists()

    @property
    def is_complete(self: Scan) -> bool:
        """Return true if the scan_completed file exists."""
        return self._scan_completed_file.exists()
