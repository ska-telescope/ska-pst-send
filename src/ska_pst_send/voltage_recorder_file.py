# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for data, weights and stats files of the PST Voltage Recorder."""
from __future__ import annotations

import os
import pathlib
import time

_all__ = [
    "VoltageRecorderFile",
]


class VoltageRecorderFile:
    """Provides representation for PST voltage recorder data and control files."""

    def __init__(self: VoltageRecorderFile, file_name: pathlib.Path, data_product_path: pathlib.Path):
        """
        Initialise the VoltageRecorderFile object.

        :param file_name: absolute path name of the file
        :param data_product_path: absolute path of the data product directory
        """
        self.file_name = file_name
        self.data_product_path = data_product_path
        self._file_number: int | None = None

    def __str__(self: VoltageRecorderFile) -> str:
        """
        Return a extended string representation of a VoltageRecorderFile object.

        :return: verbose description of the object
        :rtype: str
        """
        return (
            f"file_number={self.file_number} file_name={self.file_name} "
            + f"data_product_path={self.data_product_path}"
        )

    def __repr__(self: VoltageRecorderFile) -> str:
        """
        Return a brief string representation of a VoltageRecorderFile object.

        :return: brief description of the object
        :rtype: str
        """
        return (
            f"VoltageRecorderFile(file_number={self.file_number}, file_size={self.file_size}, "
            f"relative_path={self.relative_path})"
        )

    def __eq__(self: VoltageRecorderFile, other: object | None) -> bool:
        """
        Return the equality between two VoltageRecorderFile objects.

        :return: flag indicating object equality
        :rtype: bool
        """
        if other is None or not isinstance(other, VoltageRecorderFile):
            return False

        return (
            self.file_number == other.file_number
            and self.file_size == other.file_size
            and self.relative_path == other.relative_path
        )

    def __lt__(self: VoltageRecorderFile, other: VoltageRecorderFile) -> bool:
        """
        Return the difference between two VoltageRecorderFile objets.

        :return: flag indicating if this object is less than the other object.
        :rtype: bool
        """
        return self.file_number < other.file_number

    @property
    def age(self: VoltageRecorderFile) -> float:
        """
        Return the number of seconds since the file was last modified, or -1 if the file does not exist.

        :return: age of the file in seconds
        :rtype: int
        """
        if not self.exists():
            return -1
        return time.time() - os.path.getmtime(self.file_name)

    def exists(self: VoltageRecorderFile) -> bool:
        """
        Return true if the file exists.

        :return: flag indicating the file_name exists on the file system.
        :rtype: bool
        """
        return self.file_name.exists()

    @property
    def file_size(self: VoltageRecorderFile) -> int:
        """
        The size of the voltage recorder file in bytes.

        :return: size of the file_name in bytes.
        :rtype: int
        """
        if self.exists():
            return self.file_name.stat().st_size
        return 0

    @property
    def relative_path(self: VoltageRecorderFile) -> pathlib.Path:
        """
        The relative path to the data_product_path.

        :return: relative path to the data_product_path
        :rtype: pathlib.Path
        """
        return self.file_name.relative_to(self.data_product_path)

    @property
    def file_number(self: VoltageRecorderFile) -> int:
        """
        The file number of the voltage recorder file, or 0 in not applicable.

        The file number is used for sequencing the order of files to process.
        :return: file number or rank
        :rtype: int
        """
        if self._file_number is None:
            parts = str(self.file_name.stem).split("_")
            if len(parts) == 3:
                try:
                    self._file_number = int(parts[2])
                except ValueError:
                    self._file_number = 0
            else:
                self._file_number = 0
        return self._file_number
