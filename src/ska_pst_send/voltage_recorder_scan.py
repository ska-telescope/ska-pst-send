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
import subprocess
from typing import List, Tuple

from .metadata_builder import DadaFileManager, MetaDataBuilder
from .scan import Scan
from .voltage_recorder_file import VoltageRecorderFile

__all__ = [
    "VoltageRecorderScan",
]


class VoltageRecorderScan(Scan):
    """Class representing PST Voltage Recoder Data Products for a Scan."""

    def __init__(
        self: VoltageRecorderScan,
        data_product_path: pathlib.Path,
        relative_scan_path: pathlib.Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialise a Voltage Recorder Scan object.

        param data_product_path: base path to the `product` directory
        param relative_scan_path: path of the scan relative to the data_product_path
        param logger: python logging instance
        """
        Scan.__init__(self, data_product_path, relative_scan_path, logger)

        self._data_files: List[VoltageRecorderFile] = []
        self._weights_files: List[VoltageRecorderFile] = []
        self._stats_files: List[VoltageRecorderFile] = []
        self._config_files: List[VoltageRecorderFile] = []

    def update_files(self: Scan) -> None:
        """Check the file system for new data, weights and stats files."""
        self._data_files = [
            VoltageRecorderFile(data_file, self.data_product_path)
            for data_file in sorted(self.full_scan_path.glob("data/*.dada"))
        ]

        self._weights_files = [
            VoltageRecorderFile(weights_file, self.data_product_path)
            for weights_file in sorted(self.full_scan_path.glob("weights/*.dada"))
        ]

        self._stats_files = [
            VoltageRecorderFile(stats_file, self.data_product_path)
            for stats_file in sorted(self.full_scan_path.glob("stats/*.h5"))
        ]

        self._config_files = []
        if self.data_product_file_exists:
            self._config_files.append(VoltageRecorderFile(self._data_product_file, self.data_product_path))
        if self.scan_config_file_exists:
            self._config_files.append(VoltageRecorderFile(self._scan_config_file, self.data_product_path))

    def generate_data_product_file(self: Scan) -> bool:
        """Generate the ska-data-product.yaml file."""
        # ensure the scan is marked as completed
        if not self.is_complete:
            self.logger.warning("Cannot generate data product file as scan is not marked as completed")
            return False

        # ensure there are no unprocessed data files
        if self.next_unprocessed_file != (None, None, None):
            self.logger.warning("Cannot generate data product file as unprocessed files exist")
            return False

        data_product_file = self.full_scan_path / "ska-data-product.yaml"
        self.logger.debug(f"Generating data_product_file: {data_product_file}")

        metadata_builder = MetaDataBuilder()
        metadata_builder.dsp_mount_path = self.full_scan_path
        metadata_builder.dada_file_manager = DadaFileManager(metadata_builder.dsp_mount_path)
        metadata_builder.build_metadata()
        metadata_builder.write_metadata(filename=str(data_product_file))
        return True

    @property
    def next_unprocessed_file(
        self: Scan,
    ) -> Tuple(VoltageRecorderFile, VoltageRecorderFile, VoltageRecorderFile):
        """Return a data and weights file that have not yet been processed into a stat file."""
        self.update_files()
        for data_file in self._data_files:
            stat_file_path = self.full_scan_path / "stats" / f"{data_file.file_name.stem}.h5"
            if not stat_file_path.exists():
                file_number = data_file.file_number
                self.logger.debug(f"data_file={data_file} file_number={file_number}")
                return (
                    self._data_files[file_number],
                    self._weights_files[file_number],
                    VoltageRecorderFile(stat_file_path, self.data_product_path),
                )
        return (None, None, None)

    def process_file(
        self: Scan, unprocessed_file: Tuple(VoltageRecorderFile, VoltageRecorderFile, VoltageRecorderFile)
    ) -> bool:
        """Process the data and weights file to generate a stat file."""
        (data_file, weights_file, stats_file) = unprocessed_file

        stats_file.file_name.parent.mkdir(mode=0o644, parents=True, exist_ok=True)

        # actual command to execute when the container is setup
        command = [
            "ska_pst_stat_file_proc",
            "-d",
            str(data_file),
            "-w",
            str(weights_file),
        ]
        command = ["touch", str(stats_file.file_name)]

        # improve subprocess check UDP gen in testutils
        self.logger.info(f"running command: {command}")
        completed = subprocess.run(
            command,
            cwd=self.full_scan_path,
            shell=False,
            stdin=None,
            capture_output=True,
        )

        ok = completed.returncode == 0
        if not ok:
            self.logger.warning(f"command {command} failed: {completed}")
        return ok

    def get_all_files(self: Scan) -> List[VoltageRecorderFile]:
        """Return a list of all data, weights, stats and control files."""
        self.update_files()
        return self._data_files + self._weights_files + self._stats_files + self._config_files
