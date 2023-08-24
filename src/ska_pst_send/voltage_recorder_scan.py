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

        :param data_product_path: base path to the `product` directory
        :param relative_scan_path: path of the scan relative to the data_product_path
        :param logger: python logging instance
        """
        Scan.__init__(self, data_product_path, relative_scan_path, logger)

        self._data_files: List[VoltageRecorderFile] = []
        self._weights_files: List[VoltageRecorderFile] = []
        self._stats_files: List[VoltageRecorderFile] = []
        self._config_files: List[VoltageRecorderFile] = []
        self._unprocessable_files: List[pathlib.Path] = []

    def update_files(self: VoltageRecorderScan) -> None:
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
            for stats_file in sorted(self.full_scan_path.glob("stat/*.h5"))
        ]

        self._config_files = []
        if self.data_product_file_exists:
            self._config_files.append(VoltageRecorderFile(self._data_product_file, self.data_product_path))
        if self.scan_config_file_exists:
            self._config_files.append(VoltageRecorderFile(self._scan_config_file, self.data_product_path))

    def generate_data_product_file(self: VoltageRecorderScan) -> bool:
        """
        Generate the ska-data-product.yaml file.

        :return: flag indicating the generation is complete
        :rtype: bool
        """
        # ensure the scan is marked as completed
        if not self.is_complete:
            self.logger.warning("Cannot generate data product file as scan is not marked as completed")
            return False

        # ensure there are no unprocessed data files
        unprocessed_file = self.next_unprocessed_file(minimum_age=0)
        if unprocessed_file is not None:
            self.logger.warning(
                f"Cannot generate data product file, unprocessed files exist: {unprocessed_file}"
            )
            return False

        metadata_builder = MetaDataBuilder(dsp_mount_path=self.full_scan_path)
        metadata_builder.dada_file_manager = DadaFileManager(folder=metadata_builder.dsp_mount_path)
        metadata_builder.build_metadata()
        # this call will write to file self.full_scan_path / "ska-data-product.yaml"
        metadata_builder.write_metadata()
        return True

    def next_unprocessed_file(
        self: VoltageRecorderScan,
        minimum_age: float = 10,
    ) -> Tuple[VoltageRecorderFile, VoltageRecorderFile, VoltageRecorderFile] | None:
        """
        Return a data and weights file that have not yet been processed into a stat file.

        :param minimum_age: minimum allowed age, the number of seconds since last modification
        :return: tuple of voltage recorder files to be processed
        :rtype: Tuple[VoltageRecorderFile, VoltageRecorderFile, VoltageRecorderFile]
        """
        self.update_files()

        # combine the data and weights files into a enumerated tuple and iterate
        for (data_file, weights_file) in zip(self._data_files, self._weights_files):

            if data_file.file_number != weights_file.file_number:
                self.logger.warning(
                    f"File number mismatch data_file={data_file.file_number} "
                    f"weights_file={weights_file.file_number}"
                )
                continue

            # the stat file that should exist
            stat_file = VoltageRecorderFile(
                self.full_scan_path / "stat" / f"{data_file.file_name.stem}.h5", self.data_product_path
            )

            # if the stat file already exists, then no need to generate
            if stat_file.exists:
                continue

            # stat file cannot be generated due to a previous processing failure
            if stat_file.file_name in self._unprocessable_files:
                self.logger.debug(f"skipping {stat_file.relative_path} as is unprocessable")
                continue

            # input data and weights files must be at least minimum age
            if min(data_file.age, weights_file.age) >= minimum_age:
                self.logger.debug(f"data_file={data_file} weights_file={weights_file}")
                return (data_file, weights_file, stat_file)
        return None

    def process_file(
        self: VoltageRecorderScan,
        unprocessed_file: Tuple[VoltageRecorderFile, VoltageRecorderFile, VoltageRecorderFile],
        dir_perms: int = 0o777,
    ) -> bool:
        """
        Process the data and weights file to generate a stat file.

        :param Tuple[VoltageRecorderFile, VoltageRecorderFile, VoltageRecorderFile] unprocessed_file
        unprocessed file
        :param dir_perms: octal directory permissions to use on directory creation
        :return: flag indicating proessing was successful
        :rtype: bool
        """
        (data_file, weights_file, stats_file) = unprocessed_file

        stats_file.file_name.parent.mkdir(mode=dir_perms, parents=True, exist_ok=True)

        # actual command to execute when the container is setup
        command = [
            "ska_pst_stat_file_proc",
            "-d",
            str(data_file.file_name),
            "-w",
            str(weights_file.file_name),
        ]

        self.logger.info(f"Processing files {data_file.file_name.name}, {weights_file.file_name.name}")

        # improve subprocess check UDP gen in testutils
        self.logger.debug(f"running command: {command}")
        completed = subprocess.run(
            command,
            cwd=self.full_scan_path,
            shell=False,
            stdin=None,
            capture_output=True,
        )

        ok = completed.returncode == 0
        if not ok:
            self.logger.warning(f"command {command} failed: {completed.returncode}")
            self._unprocessable_files.append(stats_file.file_name)
        return ok

    def get_all_files(self: VoltageRecorderScan) -> List[VoltageRecorderFile]:
        """
        Return a list of all data, weights, stats and control files.

        :return: list of all pertitent files for a scan
        :rtype: List[VoltageRecorderFile]
        """
        self.update_files()
        return self._data_files + self._weights_files + self._stats_files + self._config_files
