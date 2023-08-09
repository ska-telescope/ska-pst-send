# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for writing YAML meta data files."""
from __future__ import annotations

__all__ = [
    "MetaDataBuilder",
]

import logging
import os
import pathlib
from datetime import datetime, timedelta
from decimal import Decimal

import yaml
from astropy import units as u
from astropy.coordinates import Angle, SkyCoord

from .dataproduct_file_manager import DadaFileManager
from .metadata import PstFiles, PstMetaData, PstObsCore

DEFAULT_DSP_MOUNT = "/tmp"
INTERFACE = "http://schema.skao.int/ska-data-product-meta/0.1"
CONFIG_IMAGE = "artefact.skao.int/ska-pst/ska-pst"
CONFIG_VERSION = "0.1.3"

class MetaDataBuilder:
    """Class used for building metadata files."""

    def __init__(self: MetaDataBuilder, logger: logging.Logger | None = None) -> None:
        """Create instance of PST metadata object."""
        self.logger = logger or logging.getLogger(__name__)
        self._dsp_mount_path = DEFAULT_DSP_MOUNT
        self._dada_file_manager = []
        self._pst_metadata = PstMetaData(interface=INTERFACE)

    def init_dada_file_manager(self: MetaDataBuilder) -> None:
        """Initialise DadaFileManager object.

        Called upon by the main python application after the marker file is written by ska-pst-dsp.
        """
        env_dsp_mount_path = os.environ.get("PST_DSP_MOUNT")
        self._dsp_mount_path = env_dsp_mount_path if env_dsp_mount_path else "/tmp"
        self._dada_file_manager = DadaFileManager(pathlib.Path(self._dsp_mount_path))

    def build_metadata(self: MetaDataBuilder):
        """Build the PstMetaData object."""
        try:
            assert len(self._dada_file_manager.data_files) > 0, "Expected at least 1 data file"
            assert len(self._dada_file_manager.weights_files) > 0, "Expected at least 1 weights file"

            date_object = datetime.strptime(
                self.dada_file_manager.data_files[0].utc_start, "%Y-%m-%d-%H:%M:%S"
            )
            formatted_date = date_object.strftime("%Y%m%d")
            scan_id = self.dada_file_manager.data_files[0].scan_id

            self._pst_metadata.execution_block = f"eb-{formatted_date}-{scan_id}"

            self.build_context()

            self.build_config()

            self.build_files()

            self.build_obscore()

        except Exception as e:
            # Handle exceptions here, for example, log the error
            self.logger.error(f"An error occurred while building metadata: {str(e)}")

    def build_context(self: MetaDataBuilder) -> None:
        """Populate Fields used for PstContext."""
        self._pst_metadata.context.observer = self.dada_file_manager.data_files[0].observer
        self._pst_metadata.context.intent = self.dada_file_manager.data_files[0].intent
        self._pst_metadata.context.notes = self.dada_file_manager.data_files[0].notes

    def build_config(self: MetaDataBuilder) -> None:
        """Build PstConfig. Placeholder for replacing defaults."""
        self._config.image = CONFIG_IMAGE
        self._config.version = CONFIG_VERSION

    def build_files(self: MetaDataBuilder) -> None:
        """Build PstFiles used for file block in metadata file.."""
        total_data_size = 0
        total_weights_size = 0
        dada_files = []
        for index in range(0, len(self.dada_file_manager.data_files)):
            total_data_size += self.dada_file_manager.data_files[index].file_size
            total_weights_size += self.dada_file_manager.weights_files[index].file_size

        dada_files.append(
            PstFiles(
                description="Channelised voltage data raw files",
                path="data",
                size=total_data_size,
                status="done",
            )
        )
        dada_files.append(
            PstFiles(
                description="Channelised weights raw files",
                path="weights",
                size=total_weights_size,
                status="done",
            )
        )
        self._pst_metadata.files = dada_files

    def convert_utc_to_mjd(
        self: MetaDataBuilder,
        utc_datetime: str,
        datetime_format: str = "%Y-%m-%d-%H:%M:%S",
    ) -> str:
        """Convert datetime UTC format to MJD."""
        date_object = datetime.strptime(utc_datetime, datetime_format)

        # Calculate Julian Date (including fractional part)
        days_since_2000_01_01 = (date_object - datetime(2000, 1, 1)).total_seconds() / (24 * 3600)
        jd = days_since_2000_01_01 + 2451544.5

        # Calculate Modified Julian Date (MJD)
        mjd = jd - 2400000.5

        # Round to the desired accuracy
        rounded_mjd = round(mjd, 10)

        return str(Decimal(rounded_mjd))

    def build_obscore(self: MetaDataBuilder) -> None:
        """Build PstObsCore used for obscore block in metadata file."""
        # Grab fields from header file
        first_file = self.dada_file_manager.data_files[0]
        utc_start = first_file.utc_start
        scan_id = first_file.scan_id
        tsamp = float(first_file.tsamp)
        npol = int(first_file.npol)
        nchan = int(first_file.nchan)
        freq = float(first_file.freq)
        bw = float(first_file.bw)
        stt_crd1 = first_file.stt_crd1
        stt_crd2 = first_file.stt_crd2

        # Populate metadata fields using the header
        obs_id = scan_id
        target_name = self.dada_file_manager.data_files[0].source

        dec_decimal = Angle(stt_crd2, unit="degree")

        # Convert the Angle to the sexagesimal format
        dec_sexagesimal = dec_decimal.to_string(unit="hourangle", sep=":")
        sky_coord = SkyCoord(
            f"{stt_crd1} {dec_sexagesimal}",
            equinox="J2000",
            unit=(u.hourangle, u.deg),
        )

        s_ra = float(sky_coord.ra.hour)
        s_dec = float(sky_coord.dec.deg)

        t_min = self.convert_utc_to_mjd(utc_start)

        datetime_t_min = datetime.strptime(utc_start, "%Y-%m-%d-%H:%M:%S")
        # Convert seconds to add string to float
        seconds_to_add = float(tsamp) / 1000000.0

        # Add seconds to the datetime object
        datetime_with_seconds_added = datetime_t_min + timedelta(seconds=seconds_to_add)
        utc_format = "%Y-%m-%d-%H:%M:%S.%f"
        t_max = self.convert_utc_to_mjd(datetime_with_seconds_added.strftime(utc_format), utc_format)

        # Convert microseconds to seconds
        t_resolution = float(tsamp) / 1000000.0

        # This is effectively the observation length
        t_exptime = tsamp

        data_files = self._pst_metadata.files[0]
        total_data_size = data_files.size
        total_header_size = 0

        for f in self.dada_file_manager.data_files:
            total_header_size += f.header_size

        access_estsize = total_data_size - total_header_size

        instrument_name = first_file.telescope.upper().replace("SKA", "SKA-")

        pol_xel = npol

        # Polarisations are not detected, expect a value of X, Y
        # best not to define it (keep it as null)
        pol_states = "null"

        em_xel = nchan
        em_unit = "Hz"

        em_min = (freq - (bw / 2)) * 1e6
        em_max = (freq + (bw / 2)) * 1e6

        em_res_power = "null"

        # Value of Resolution along the spectral axis".
        # Not sure about overampling here...
        em_resolution = (bw / nchan) * 1e6

        # Unified Content Descriptor of observable,
        # not really anything suitable for PST. Put null for now.
        o_ucd = "null"

        """
        TODO: The following are to be populated after confirming their source.
        dataproduct_type=dataproduct_type,
        dataproduct_subtype=dataproduct_subtype,
        calib_level=calib_level,
        """
        obscore = PstObsCore(
            obs_id=obs_id,
            access_estsize=access_estsize,
            target_name=target_name,
            s_ra=s_ra,
            s_dec=s_dec,
            t_min=t_min,
            t_max=t_max,
            t_resolution=t_resolution,
            t_exptime=t_exptime,
            instrument_name=instrument_name,
            pol_xel=pol_xel,
            pol_states=pol_states,
            em_xel=em_xel,
            em_unit=em_unit,
            em_min=em_min,
            em_max=em_max,
            em_res_power=em_res_power,
            em_resolution=em_resolution,
            o_ucd=o_ucd,
        )

        self._pst_metadata.obscore = obscore

    def write_metadata(self: MetaDataBuilder, file_name: str = "ska-data-product.yaml"):
        """Write YAML object to a YAML file."""
        absolute_path = f"{self._dsp_mount_path}/{file_name}"
        with open(absolute_path, "w") as yaml_file:
            yaml.dump(self.pst_metadata.to_dict(), yaml_file)

    @property
    def dada_file_manager(self: MetaDataBuilder) -> DadaFileManager:
        """Getter public method.

        dada_file_manager as a property of MetaDataBuilder.
        """
        return self._dada_file_manager

    @property
    def dsp_mount_path(self: MetaDataBuilder) -> str:
        """Getter public method.

        dsp_mount_path as a property of MetaDataBuilder.
        """
        return self._dsp_mount_path

    @dsp_mount_path.setter
    def dsp_mount_path(self: MetaDataBuilder, path: str) -> None:
        """Setter method.

        dsp_mount_path as a property of MetaDataBuilder.
        param path: Absolute path containing dada files.
        """
        self._dsp_mount_path = path
        if self._dada_file_manager:
            self._dada_file_manager.set_dsp_mount_path(path)

    @property
    def pst_metadata(self: MetaDataBuilder) -> PstMetaData:
        """Getter public method.

        PstMetaData as a property of MetaDataBuilder.
        """
        return self._pst_metadata
