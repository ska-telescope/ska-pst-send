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
import time
from typing import Any, List, Tuple

from .metadata_builder import MetaDataBuilder
from .scan import Scan
from .voltage_recorder_file import VoltageRecorderFile

__all__ = [
    "VoltageRecorderScan",
]

NANOSECONDS_PER_SEC = 1e9


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

        # create time of scan is creation time of scan directory
        created_time_ns = self.full_scan_path.stat().st_ctime_ns
        self._created_time_ns: int = created_time_ns
        self._modified_time_ns: int = created_time_ns

        # state variables for processing and transferring
        self.processing_failed = False
        self.transfer_failed = False
        self.update_files()

    @property
    def modified_time_secs(self: VoltageRecorderScan) -> float:
        """Get last modified time in seconds."""
        return self._modified_time_ns / NANOSECONDS_PER_SEC

    def is_valid(self: VoltageRecorderScan) -> bool:
        """Get whether the the scan is still valid or not.

        A valid scan matches the following conditions:
            * file processing hasn't failed
            * file transfer hasn't failed
            * the file directory still exists
        """
        return self.path_exists() and not self.processing_failed and not self.transfer_failed

    def update_modified_time(self: VoltageRecorderScan) -> None:
        """Update the last time the scan was processed."""
        curr_time_ns = time.time_ns()
        self.logger.debug(
            f"updating modified time for scan {self.scan_id} to {curr_time_ns / NANOSECONDS_PER_SEC}"
        )
        self._modified_time_ns = curr_time_ns

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
        if self.data_product_file_exists():
            self._config_files.append(VoltageRecorderFile(self._data_product_file, self.data_product_path))
        if self.scan_config_file_exists():
            self._config_files.append(VoltageRecorderFile(self._scan_config_file, self.data_product_path))

        def _update_last_modified_time(files: List[VoltageRecorderFile]) -> None:
            for f in files:
                file_modified_time_ns = f.file_name.stat().st_mtime_ns
                if file_modified_time_ns > self._modified_time_ns:
                    self.logger.debug(
                        f"file {f} has modified file more recent than scan's modified time. "
                        f"Updating scan's modified time to {file_modified_time_ns / NANOSECONDS_PER_SEC}"
                    )
                    self._modified_time_ns = file_modified_time_ns

        for files in [
            self._data_files,
            self._weights_files,
            self._stats_files,
            self._config_files,
        ]:
            _update_last_modified_time(files)

    def generate_data_product_file(self: VoltageRecorderScan) -> None:
        """Generate the ska-data-product.yaml file."""
        # ensure the scan is marked as completed
        assert self.is_complete(), "generate_data_product_file called when scan is not complete"
        unprocessed_file = self.next_unprocessed_file(minimum_age=0)
        assert (
            unprocessed_file is None
        ), f"generate_data_product_file called when there are unprocessed files. {unprocessed_file}"

        metadata_builder = MetaDataBuilder(dsp_mount_path=self.full_scan_path)
        metadata_builder.generate_metadata()

    def _data_and_weights_file_pairs(
        self: VoltageRecorderScan,
    ) -> List[Tuple[VoltageRecorderFile, VoltageRecorderFile]]:
        return [
            (d, w) for d in self._data_files for w in self._weights_files if d.file_number == w.file_number
        ]

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
        for (data_file, weights_file) in self._data_and_weights_file_pairs():
            # the stat file that should exist
            stat_file = VoltageRecorderFile(
                self.full_scan_path / "stat" / f"{data_file.file_name.stem}.h5", self.data_product_path
            )

            # stat file cannot be generated due to a previous processing failure
            if stat_file.file_name in self._unprocessable_files:
                self.logger.debug(
                    f"{self} skipping {stat_file.relative_path} as it has been marked as unprocessable"
                )
                continue

            # if the stat file already exists, then no need to generate
            if stat_file.exists():
                continue

            # input data and weights files must be at least minimum age
            if min(data_file.age, weights_file.age) >= minimum_age:
                self.logger.debug(
                    f"{self} has unprocessed pair of files. data_file={data_file} weights_file={weights_file}"
                )
                return (data_file, weights_file, stat_file)

        return None

    def process_next_unprocessed_file(self: VoltageRecorderScan, minimum_age: float = 10.0) -> None:
        """Process the next unprocessed file if one exists.

        :param minimum_age: minimum allowed age, the number of seconds since last modification
        :return: True if a file was processed else False
        """
        self.logger.debug(f"Trying to find next unprocessed file with minimum age of {minimum_age}")
        unprocessed_file = self.next_unprocessed_file(minimum_age=minimum_age)
        self.logger.debug(f"unprocessed_file={unprocessed_file}")
        if unprocessed_file is not None:
            self.process_file(unprocessed_file)

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
        self.logger.debug(f"{self} processing {unprocessed_file}")
        (data_file, weights_file, stats_file) = unprocessed_file

        self.logger.debug(f"ensuring {stats_file.file_name.parent} exists")
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
            self.logger.debug(f"marking {stats_file.file_name} as unprocessable file")
            self._unprocessable_files.append(stats_file.file_name)

        self.update_modified_time()
        return ok

    def get_all_files(self: VoltageRecorderScan) -> List[VoltageRecorderFile]:
        """
        Return a list of all data, weights, stats and control files.

        :return: list of all pertitent files for a scan
        :rtype: List[VoltageRecorderFile]
        """
        self.update_files()
        return [*self._data_files, *self._weights_files, *self._stats_files, *self._config_files]

    def __repr__(self: VoltageRecorderScan) -> str:
        """Get string representation of current VoltageRecorderScan."""
        return (
            f"VoltageRecorderScan(eb_id={self.eb_id}, "
            f"subsystem_id={self.subsystem_id}, scan_id={self.scan_id})"
        )

    @staticmethod
    def compare_modified(first: VoltageRecorderScan, second: VoltageRecorderScan) -> int:
        """Compare two scan objects by modified time to allow for sorting.

        This implementation compares 2 scans by modified time, creation time, scan id and
        finally eb id. The scan that was modified the least recently will be ordered before
        scans modified more recently. Comparison by creation time, scan id and eb-id are
        to break ties.

        As the modified time can be updated on scans the use of this comparator is should
        not be used to sort dictionaries.

        :param first: in the A < B comparison, this parameter is A
        :param second: in the A < B comparison, this parameter is B
        """
        # used to reduce complexity of function as each attributed would do
        # the same thing.
        def _cmp(first_attr: Any, second_attr: Any) -> int:
            if first_attr < second_attr:
                return -1
            if first_attr > second_attr:
                return 1
            return 0

        for attr_name in ["_modified_time_ns", "_created_time_ns", "scan_id", "eb_id"]:
            first_attr = getattr(first, attr_name)
            second_attr = getattr(second, attr_name)

            comp = _cmp(first_attr, second_attr)
            if comp != 0:
                return comp

        return 0
