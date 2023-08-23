# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for managing DADA files."""
from __future__ import annotations

import logging
import mmap
import pathlib
from types import TracebackType
from typing import Any, Dict, List, Tuple

import nptyping as npt

__all__ = [
    "DadaFileManager",
    "DadaFileReader",
    "WeightsFileReader",
]


DEFAULT_HEADER_SIZE = 4096
HEADER_SIZE_KEY = "HDR_SIZE"
SECONDS_PER_FILE = 10
ScalesType = npt.NDArray[Any, npt.Single]
WeightsType = npt.NDArray[Any, npt.UShort]


class DadaFileManager:
    """Class that captures PST data files.

    Parses attributes from a set of PST voltage recorder data and weights files and computes some of the
    derived quantities from the scales and weights, such as the inferred number of dropped/invalid packets.
    """

    def __init__(
        self: DadaFileManager,
        folder: pathlib.Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Init object.

        param folder: The absolute path containing the dada files.
        """
        assert folder.exists() and folder.is_dir()
        self.folder = folder
        self._header: Dict[str, str] = {}
        self._data_files: List[DadaFileReader] = []
        self._weights_files: List[WeightsFileReader] = []
        self.logger = logger or logging.getLogger(__name__)
        self._get_dada_files()

    def _get_dada_files(self: DadaFileManager) -> None:
        """Populate list of Data and Weights files."""
        data_paths = list(self.folder.glob("data/*.dada"))
        weights_paths = list(self.folder.glob("weights/*.dada"))
        assert len(data_paths) == len(
            weights_paths
        ), f"data_paths {len(data_paths)}!=weights_paths {len(weights_paths)}"

        data_paths.sort()
        weights_paths.sort()
        data_files = [DadaFileReader(f) for f in data_paths]
        weights_files = [WeightsFileReader(f) for f in weights_paths]

        self._data_files = data_files
        self._weights_files = weights_files

    @property
    def data_files(self: DadaFileManager) -> List[DadaFileReader]:
        """Get list of DadaFileReader objects."""
        return self._data_files

    @property
    def weights_files(self: DadaFileManager) -> List[WeightsFileReader]:
        """Get list of WeightsFileReader objects."""
        return self._weights_files


class DadaFileReader:
    """Class that can be used to read a PSR DADA file."""

    def __init__(
        self: DadaFileReader,
        file: pathlib.Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Create instance of file reader."""
        assert file.exists() and file.is_file()
        self.file = file
        self.header_size = DEFAULT_HEADER_SIZE
        self._header: Dict[str, str] = {}
        self.logger = logger or logging.getLogger(__name__)
        self._read_header()

    def __enter__(self: DadaFileReader) -> DadaFileReader:
        """Enter context manager for this file."""
        self._read_header()
        return self

    def __exit__(
        self: DadaFileReader,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager."""

    def _read_header(self: DadaFileReader) -> Dict[str, str]:
        """Read the header of file."""
        with open(self.file, "rb") as f:
            # memory map file - just want the first 4096 bytes
            with mmap.mmap(f.fileno(), DEFAULT_HEADER_SIZE, prot=mmap.PROT_READ) as mm:
                header, header_str = self._read_header_from_mmap(mm)

            # if key doesn't exist or its not an int we expect this to fail
            self.header_size = int(header[HEADER_SIZE_KEY])
            if self.header_size != DEFAULT_HEADER_SIZE:
                with mmap.mmap(f.fileno(), self.header_size, prot=mmap.PROT_READ) as mm:
                    header, header_str = self._read_header_from_mmap(mm)

            self.logger.debug(f"Header from file {self.file}:\n{header_str}")
            self._header = header
            return header

    def _read_header_from_mmap(self: DadaFileReader, file: mmap.mmap) -> Tuple[Dict[str, str], str]:
        """Read the lines of the memory mapped file into a dictionary."""
        header: Dict[str, str] = {}

        # this is only used for loggin:
        header_str = ""
        for currline in iter(file.readline, b""):
            line: str = currline.decode()
            line = line.replace("\0", " ").strip()

            # ignore a comment
            if line.startswith("#"):
                continue

            if len(line) == 0:
                continue

            header_str += line
            header_str += "\n"

            [key, value] = line.lstrip().split(" ", maxsplit=1)
            assert len(key) > 0, f"Expected header key of line {str(currline)} to not be empty"
            header[key] = value.lstrip()

        return header, header_str

    @property
    def header(self: DadaFileReader) -> Dict[str, str]:
        """Get header for file."""
        return {**self._header}

    @property
    def file_path(self: DadaFileReader) -> str:
        """Get path of file in string."""
        return str(self.file.resolve())

    @property
    def file_size(self: DadaFileReader) -> int:
        """Get size of file in bytes."""
        stats = self.file.stat()
        return stats.st_size

    @property
    def data_size(self: DadaFileReader) -> int:
        """Get the size of the data."""
        return self.file_size - self.header_size

    @property
    def obs_offset(self: DadaFileReader) -> int:
        """Get the OBS_OFFSET value."""
        return int(self._header["OBS_OFFSET"])

    @property
    def file_number(self: DadaFileReader) -> int:
        """Get the FILE_NUMBER value from header."""
        return int(self._header["FILE_NUMBER"])

    @property
    def scan_id(self: DadaFileReader) -> int:
        """Get the SCAN_ID value from header."""
        return int(self._header["SCAN_ID"])

    @property
    def observer(self: DadaFileReader) -> str:
        """Get the OBSERVER value from header."""
        return self._header["OBSERVER"]

    @property
    def intent(self: DadaFileReader) -> str:
        """Build value using SOURCE from header."""
        return f"Tied-array beam observation of {self._header['SOURCE']}"

    @property
    def notes(self: DadaFileReader) -> str:
        """Get the NOTES value from header."""
        # self._header['INTENT'] key error
        return "notes TBD"

    @property
    def source(self: DadaFileReader) -> str:
        """Get the SOURCE value from header."""
        return self._header["SOURCE"]

    @property
    def utc_start(self: DadaFileReader) -> str:
        """Get the UTC_START value from header."""
        return self._header["UTC_START"]

    @property
    def tsamp(self: DadaFileReader) -> str:
        """Get the TSAMP value from header."""
        return self._header["TSAMP"]

    @property
    def telescope(self: DadaFileReader) -> str:
        """Get the TELESCOPE value from header."""
        return self._header["TELESCOPE"]

    @property
    def nchan(self: DadaFileReader) -> str:
        """Get the NCHAN value from header."""
        return self._header["NCHAN"]

    @property
    def freq(self: DadaFileReader) -> str:
        """Get the FREQ value from header."""
        return self._header["FREQ"]

    @property
    def bw(self: DadaFileReader) -> str:
        """Get the BW value from header."""
        return self._header["BW"]

    @property
    def npol(self: DadaFileReader) -> str:
        """Get the NPOL value from header."""
        return self._header["NPOL"]

    @property
    def stt_crd1(self: DadaFileReader) -> str:
        """Get the STT_CRD1 value from header."""
        return self._header["STT_CRD1"]

    @property
    def stt_crd2(self: DadaFileReader) -> str:
        """Get the STT_CRD2 value from header."""
        return self._header["STT_CRD2"]


LOW_BAND_CONFIG = {
    "udp_format": "LowPST",
    "packet_nchan": 24,
    "packet_nsamp": 32,
    "packets_per_buffer": 16,
    "num_of_buffers": 64,
    "oversampling_ratio": [4, 3],
}

COMMON_MID_CONFIG = {
    "packet_nchan": 185,
    "packet_nsamp": 4,
    "oversampling_ratio": [8, 7],
}

MID_BAND_CONFIG = {
    "1": {
        **COMMON_MID_CONFIG,
        "udp_format": "MidPSTBand1",
        "packets_per_buffer": 1024,
        "num_of_buffers": 128,
    },
    "2": {
        **COMMON_MID_CONFIG,
        "udp_format": "MidPSTBand2",
        "packets_per_buffer": 1024,
        "num_of_buffers": 128,
    },
    "3": {
        **COMMON_MID_CONFIG,
        "udp_format": "MidPSTBand3",
        "packets_per_buffer": 512,
        "num_of_buffers": 256,
    },
    "4": {
        **COMMON_MID_CONFIG,
        "udp_format": "MidPSTBand4",
        "packets_per_buffer": 512,
        "num_of_buffers": 256,
    },
    "5a": {
        **COMMON_MID_CONFIG,
        "udp_format": "MidPSTBand5",
        "packets_per_buffer": 512,
        "num_of_buffers": 256,
    },
    "5b": {
        **COMMON_MID_CONFIG,
        "udp_format": "MidPSTBand5",
        "packets_per_buffer": 512,
        "num_of_buffers": 256,
    },
}

# this inverts the frequency band configs to being a UDP format config
# Band 5a and 5b have the same udp_format
UDP_FORMAT_CONFIG = {
    "LowPST": LOW_BAND_CONFIG,
    **{config["udp_format"]: config for (freq_band, config) in MID_BAND_CONFIG.items() if freq_band != "5b"},
}


class WeightsFileReader(DadaFileReader):
    """Class used to read Weights PSRDADA generated by ska_pst_dsp_disk."""

    def __init__(
        self: WeightsFileReader,
        file: pathlib.Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Create instance of weights file reader."""
        super().__init__(file, logger=logger)

        self._scales: ScalesType | None = None
        self._weights: WeightsType | None = None

    def __enter__(self: WeightsFileReader) -> WeightsFileReader:
        """Enter context manager for this file."""
        self._read_data()
        return self

    def __exit__(
        self: WeightsFileReader,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager for this file."""

    def _read_data(self: WeightsFileReader) -> None:
        """Read the scales and weights in the file."""
        self._read_header()

        # extract the required parameters from the header
        udp_format = self._header["UDP_FORMAT"]

        # the CBF to PSR ICD specifies all weights a 16 bits per sample
        assert self.nbit == 16, f"Expected nbit={self.nbit} to be 16"

        # compute the number of relative weights in each packet
        packet_nsamp = WeightsFileReader.get_udp_format_config(udp_format)["packet_nsamp"]

        msg = f"""Expect packet_nsamp={packet_nsamp}
        a multiple of {self.nsamp_per_weight}"""
        assert packet_nsamp % self.nsamp_per_weight == 0, msg
        self.nweight_per_packet = packet_nsamp // self.nsamp_per_weight
        self.logger.debug(f"computed weights per packet as {self.nweight_per_packet}")

        # compute the number of channels in each packet
        assert self.packet_weights_size % (self.nweight_per_packet * self.nbit // 8) == 0, (
            f"Expected packet_weights_size={self.packet_weights_size} to be a "
            f"multiple of {self.nweight_per_packet * self.nbit // 8}"
        )
        self.nchan_per_packet = self.packet_weights_size // (self.nweight_per_packet * self.nbit // 8)
        msg = f"""
               packet_weights_size={self.packet_weights_size}
               nweight_per_packet={self.nweight_per_packet}
               nbit={self.nbit}
               nchan_per_packet={self.nchan_per_packet}
               """
        self.logger.debug(msg)

        self.weights_packet_stride = self.packet_weights_size + self.packet_scales_size

        msg = f"""
               weights_packet_stride={self.weights_packet_stride}
               packet_scales_size={self.packet_scales_size}
               packet_weights_size={self.packet_weights_size}
               """
        self.logger.debug(msg)

        with open(self.file, "rb") as f:
            # memory map file - want all bytes after the header
            with mmap.mmap(
                f.fileno(),
                self.data_size,
                prot=mmap.PROT_READ,
                offset=self.header_size,
            ) as mm:
                self._read_data_from_mmap(mm)

    def _read_data_from_mmap(self: WeightsFileReader, file: mmap.mmap) -> None:
        """Read the scales and weights in the memory mapped file."""
        # weights are written to file in the order:
        msg = f"""
               Expected data_size={self.data_size} a
               multiple of {self.weights_packet_stride}
               """
        assert self.data_size % self.weights_packet_stride == 0, msg
        num_packets = self.data_size // self.weights_packet_stride

        # packets are organised into heaps, where a heap contains all
        # the scale factors and weights for all the channels
        msg = f"""
               Expected nchan={self.nchan} a
               multiple of {self.nchan_per_packet}
               """
        assert self.nchan % self.nchan_per_packet == 0, msg
        packets_per_heap = self.nchan // self.nchan_per_packet

        # may not get a full heap at the end of the file
        num_heaps = num_packets // packets_per_heap
        if num_packets % packets_per_heap != 0:
            num_heaps + 1

        self.logger.debug(
            (
                f"data_size={self.data_size}, num_packets={num_packets} "
                f"packets_per_heap={packets_per_heap} num_heaps={num_heaps}"
            )
        )

        # no need to assert that nbit % 8 is 0 as
        # we have already asserted it is 16
        nbit_as_bytes = self.nbit // 8
        msg = f"""
               Expected packet_weights_size={self.packet_weights_size}
               a multiple of {nbit_as_bytes}
               """
        assert self.packet_weights_size % nbit_as_bytes == 0, msg

    @staticmethod
    def get_udp_format_config(udp_format: str) -> dict:
        """Get the UDP format configuration.

        This will assert that the udp_format is valid.

        This will return the configuration that is specific to a UDP format.
        This is related to the frequency band config
        returned by :py:func:`get_frequency_band_config`
        but uses the UDP format as a key not the frequency band.

        The keys that are returned are:
            * udp_format
            * packet_nchan
            * packet_nsamp
            * packets_per_buffer
            * num_of_buffers
            * oversampling_ratio

        An example output is as follows::

            {
                "udp_format": "LowPST",
                "packet_nchan": 24,
                "packet_nsamp": 32,
                "packets_per_buffer": 16,
                "num_of_buffers": 64,
                "oversampling_ratio": [4, 3],
            }

        :param udp_format: the UDP formate to get configuration for
        :type udp_format: str
        :return: a dictionary of configuration for the UDP format.
        :rtype: Dict[str, Any]
        """
        msg = f"""
               Expected {udp_format} in the UDP_FORMAT_CONFIG.
               Valid keys are {UDP_FORMAT_CONFIG.keys()}
               """
        assert udp_format in UDP_FORMAT_CONFIG, msg
        return UDP_FORMAT_CONFIG[udp_format]

    @property
    def packet_offset(self: WeightsFileReader) -> int:
        """Get the package offset for current file.

        This converts the obs_offset a packet offset by dividing the value
        by the weights_packet_stride. This will assert that the obs_offset
        is a mulitple of weights_packet_stride
        """
        # offset the packet index by the packet_offset deduced
        # from the OBS_OFFSET
        msg = f"""
               Expected obs_offset={self.obs_offset} to be
               a multiple of {self.weights_packet_stride}
               """
        assert self.obs_offset % self.weights_packet_stride == 0, msg
        return self.obs_offset // self.weights_packet_stride

    @property
    def nbit(self: WeightsFileReader) -> int:
        """Get the number of bits the data is encoded in."""
        return int(self._header["NBIT"])

    @property
    def nsamp_per_weight(self: WeightsFileReader) -> int:
        """Get the number of samples the weights are used for."""
        return int(self._header["NSAMP_PER_WEIGHT"])

    @property
    def packet_weights_size(self: WeightsFileReader) -> int:
        """Get the packet weights size."""
        return int(self._header["PACKET_WEIGHTS_SIZE"])

    @property
    def packet_scales_size(self: WeightsFileReader) -> int:
        """Get the packet scales size."""
        return int(self._header["PACKET_SCALES_SIZE"])
