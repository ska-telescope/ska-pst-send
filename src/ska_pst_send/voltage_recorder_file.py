# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for data, weights and stats files of the PST Voltage Recorder."""
from __future__ import annotations

import pathlib

_all__ = [
    "VoltageRecorderFile",
]


class VoltageRecorderFile:
    """Provides representation for PST voltage recorder data and control files."""

    def __init__(self: VoltageRecorderFile, file_name: pathlib.Path, data_product_path: pathlib.Path):
        """Initialise the VoltageRecorderFile object."""
        self.file_name = file_name
        self.data_product_path = data_product_path
        self.file_number = self.get_file_number(file_name)

    def __str__(self: VoltageRecorderFile):
        """Return a extended string representation of a VoltageRecorderFile object."""
        return (
            f"file_number={self.file_number} file_name={self.file_name} "
            + f"data_product_path={self.data_product_path}"
        )

    def __repr__(self: VoltageRecorderFile):
        """Return a brief string representation of a VoltageRecorderFile object."""
        return f"{self.relative_path}"

    def __eq__(self: VoltageRecorderFile, other: VoltageRecorderFile) -> bool:
        """Return the equality between two VoltageRecorderFile objects."""
        if other is None:
            return False
        return (
            self.file_number == other.file_number
            and self.file_size == other.file_size
            and self.relative_path == other.relative_path
        )

    def __lt__(self: VoltageRecorderFile, other: VoltageRecorderFile) -> bool:
        """Return the difference between two VoltageRecorderFile objets."""
        return self.file_number < other.file_number

    @property
    def exists(self: VoltageRecorderFile) -> bool:
        """Return true if the file exists."""
        return self.file_name.exists()

    @property
    def file_size(self: VoltageRecorderFile) -> int:
        """The size of the voltage recorder file in bytes."""
        if self.exists:
            return self.file_name.stat().st_size
        return 0

    @property
    def relative_path(self: VoltageRecorderFile) -> pathlib.Path:
        """The relative path to the data_product_path."""
        return self.file_name.relative_to(self.data_product_path)

    @classmethod
    def get_file_number(self: VoltageRecorderFile, file_name: pathlib.Path) -> int:
        """Return the file number of the voltage recorder file or 0 if no file number is relevant."""
        parts = str(file_name.stem).split("_")
        if len(parts) == 3:
            try:
                return int(parts[2])
            except ValueError:
                return 0
        return 0
