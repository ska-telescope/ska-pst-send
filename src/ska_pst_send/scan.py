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
import subprocess
from dataclasses import dataclass, field
from typing import List, Tuple

from .metadata_builder import DadaFileManager, MetaDataBuilder

__all__ = [
    "Scan",
]


class Scan:
    """Base class for representing Data Products from PST Scans that are stored on the local file system."""

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
        self.logger = logger

        assert self.data_product_path.exists() and self.data_product_path.is_dir()
        # assert self.full_scan_path.exists() and self.full_scan_path.is_dir()

        self._scan_config_file = self.full_scan_path / "scan-config.json"
        self._data_product_file = self.full_scan_path / "ska-data-product.yaml"
        self._scan_completed_file = self.full_scan_path / "scan_completed"

        # assert self._scan_config_file.is_file()

    def match_full_path(self: Scan, full_scan_path: pathlib.Path) -> bool:
        """Return true if the full_scan_path matches the scan_path."""
        return self.full_scan_path.resolve() == full_scan_path.resolve()

    def match_relative_path(self: Scan, relative_scan_path: pathlib.Path) -> bool:
        """Return true if the full_scan_path matches the scan_path."""
        return self.relative_scan_path == relative_scan_path

    @property
    def is_scan_recording(self: Scan) -> bool:
        """Return true is the scan been not yet been marked as completed."""
        return not self._scan_completed_file.is_file()

    @property
    def data_product_file_exists(self: Scan) -> bool:
        """Return true if the ska-pst-dataproduct.yaml file exists."""
        return self._data_product_file.is_file()

    @property
    def scan_config_file_exists(self: Scan) -> bool:
        """Return true if the scan-config.json file exists."""
        return self._scan_config_file.is_file()

    @property
    def scan_completed_exists(self: Scan) -> bool:
        """Return true if the scan_completed file exists."""
        return self._scan_completed_file.is_file()


@dataclass(order=True)
class VoltageRecorderFile:
    file_number: int
    prefix_path: pathlib.Path = field(compare=False)
    file_name: pathlib.Path = field(compare=False)
    file_size: int


class VoltageRecorderScan(Scan):
    """Class representing PST Voltage Recoder Data Products for a Scan."""

    def __init__(
        self: VoltageRecorderScan,
        data_product_path: pathlib.Path,
        relative_scan_path: pathlib.Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialise a Voltage Recorder Scan object.

        param data_product_path: base path to the /product directory
        param relative_scan_path: path of the scan relative to the data_product_path
        param logger: python logging instance
        """
        Scan.__init__(self, data_product_path, relative_scan_path, logger)

        self._data_files: List[VoltageRecorderFile] = []
        self._weights_files: List[VoltageRecorderFile] = []
        self._stats_files: List[VoltageRecorderFile] = []
        self._config_files: List[VoltageRecorderFile] = []
        self.update_files()

    def update_files(self: Scan) -> int:
        """Check the file system for new data, weights and stats files.

        Returns the number of files changed since the previous call to this method
        """
        prev_files_len = (
            len(self._data_files)
            + len(self._weights_files)
            + len(self._stats_files)
            + len(self._config_files)
        )

        self._data_files = []
        for data_file in list(self.full_scan_path.glob("data/*.dada")):
            self._data_files.append(self.get_voltage_recorder_file(data_file))

        self._weights_files = []
        for weights_file in list(self.full_scan_path.glob("weights/*.dada")):
            self._weights_files.append(self.get_voltage_recorder_file(weights_file))

        self._stats_files = []
        for stats_file in list(self.full_scan_path.glob("stats/*.h5")):
            self._stats_files.append(self.get_voltage_recorder_file(stats_file))

        self._config_files = []
        if self.data_product_file_exists:
            self._config_files.append(self.get_config_file(self._data_product_file))
        if self.scan_config_file_exists:
            self._config_files.append(self.get_config_file(self._scan_config_file))

        return (
            len(self._data_files)
            + len(self._weights_files)
            + len(self._stats_files)
            + len(self._config_files)
            - prev_files_len
        )

    def get_config_file(self: Scan, config_file_path: pathlib.Path) -> VoltageRecorderFile:
        """Return a VoltageRecorderFile dataclass object for the config file."""
        file_number = 0
        prefix = self.data_product_path
        config_file = pathlib.Path(os.path.relpath(config_file_path, self.data_product_path))
        file_size = self.get_file_size(config_file_path)
        return VoltageRecorderFile(file_number, prefix, config_file, file_size)

    def get_voltage_recorder_file(self: Scan, data_file: pathlib.Path) -> VoltageRecorderFile:
        """Return a VoltageRecorderFile dataclass object for the data file."""
        file_number = self.get_file_number(data_file)
        prefix = self.data_product_path
        scan_file = pathlib.Path(os.path.relpath(data_file, self.data_product_path))
        file_size = self.get_file_size(data_file)
        return VoltageRecorderFile(file_number, prefix, scan_file, file_size)

    def get_file_number(self: Scan, file_path: pathlib.Path) -> int:
        """Return the file number field of the data, weights or stats filename."""
        file_name_stem = str(file_path.stem)
        parts = file_name_stem.split("_")
        assert len(parts) == 3, "Expected file_path to have stem with 3 underscore delimited components."
        file_number = int(parts[2])
        # self.logger.debug(f"file_path={file_path} file_number={file_number}")
        return file_number

    def get_file_size(self: Scan, data_file: pathlib.Path) -> int:
        """Get size of file in bytes."""
        stats = data_file.stat()
        return stats.st_size

    def generate_data_product_file(self: Scan):
        """Generate the ska-data-product.yaml file."""
        # ensure the scan is marked as completed
        if not self.is_scan_completed:
            self.logger.warning("Cannot generate data product file as scan is not marked as completed")
            return False

        # ensure there are no unprocessed data files
        (data_file, weights_file) = self.get_unprocessed_file()
        if not (data_file is None and weights_file is None):
            self.logger.warning("Cannot generate data product file as unprocessed files exist")
            return False

        data_product_file = self.full_scan_path / pathlib.Path("ska-data-product.yaml")
        self.logger.debug(f"Generating data_product_file: {data_product_file}")

        metadata_builder = MetaDataBuilder()
        metadata_builder.dsp_mount_path = self.full_scan_path
        metadata_builder.dada_file_manager = DadaFileManager(metadata_builder.dsp_mount_path)
        metadata_builder.build_metadata()
        metadata_builder.write_metadata(filename=str(data_product_file))
        return True

    def delete_scan(self: Scan):
        """Delete all the local data files associated with a scan."""
        # TODO decide if a Scan can delete itself

    def get_unprocessed_file(
        self: Scan,
    ) -> Tuple(pathlib.path, pathlib.path, pathlib.path):
        """Return a data and weights file that have not yet been processed into a stat file."""
        self.update_files()
        for data_file in self._data_files:
            expected_stat_file = pathlib.Path("stats") / pathlib.Path(f"{data_file.file_name.stem}.h5")
            expected_stat_path = self.full_scan_path / expected_stat_file
            if not expected_stat_path.is_file():
                file_number = self.get_file_number(data_file.file_name)
                self.logger.debug(f"data_file={data_file} file_number={file_number}")
                return (
                    self._data_files[file_number],
                    self._weights_files[file_number],
                    expected_stat_file,
                )
        return (None, None, None)

    def process_file(self: Scan, unprocessed_file: Tuple(pathlib.path, pathlib.path, pathlib.path)):
        """Process the data and weights file to generate a stat file."""
        data_file = unprocessed_file[0]
        weights_file = unprocessed_file[1]
        stats_file = unprocessed_file[2]

        stats_path = self.full_scan_path / stats_file
        os.makedirs(os.path.dirname(stats_path), exist_ok=True)

        # actual command to execute when the container is setup
        command = [
            "ska_pst_stat_file_proc",
            "-d",
            str(data_file),
            "-w",
            str(weights_file),
        ]
        command = ["touch", str(stats_path)]

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
        return self._data_files + self._weights_files + self._stats_files + self._config_files
