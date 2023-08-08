# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST Testutils project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for writing YAML meta data files."""
from __future__ import annotations

__all__ = [
    "MetaDataBuilder",
]

import logging
import pathlib
from datetime import datetime, timedelta
from decimal import Decimal

from .dataproduct_file_manager import DadaFileManager
from .metadata import PstConfig, PstContext, PstFiles, PstMetadata, PstObsCore

DEFAULT_DSP_MOUNT = "/mnt/dsp/"
INTERFACE = "http://schema.skao.int/ska-data-product-meta/0.1"
CONTEXT_OBSERVER = "AIV_person_1"
CONTEXT_INTENT = "Tied-array beam observation"
CONFIG_IMAGE = "artefact.skao.int/ska-pst/ska-pst"
CONFIG_VERSION = "0.1.3"
OBSCORE_DATAPRODUCT_TYPE = "timeseries"
OBSCORE_DATAPRODUCT_SUBTYPE = "voltages"
OBSCORE_CALIB_LEVEL = 0
OBSCORE_FACILITY_NAME = "SKA-Observatory"
OBSCORE_INSTRUMENT_NAME = "SKA-LOW"


class MetaDataBuilder:
    """Class used for building metadata files."""

    def __init__(
        self: MetaDataBuilder, logger: logging.Logger | None = None
    ) -> None:
        """Create instance of PST metadata object."""
        self.logger = logger or logging.getLogger(__name__)
        self._dsp_mount_path = DEFAULT_DSP_MOUNT
        self._dada_file_manager = []
        self._context = PstContext(
            observer=CONTEXT_OBSERVER,
            intent=CONTEXT_INTENT,
            notes="",
        )
        self._config = PstConfig(
            image=CONFIG_IMAGE,
            version=CONFIG_VERSION,
        )
        self._pst_metadata = PstMetadata(
            interface=INTERFACE, context=self._context, config=self._config
        )

    def init_dada_file_manager(self: MetaDataBuilder) -> None:
        self._dada_file_manager = DadaFileManager(
            pathlib.Path(self._dsp_mount_path)
        )

    def build_metadata(self: MetaDataBuilder):
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

    def build_context(self: MetaDataBuilder) -> None:
        """Populate Fields used for PstContext"""
        self._pst_metadata.context.observer = (
            self.dada_file_manager.data_files[0].observer
        )
        self._pst_metadata.context.intent = self.dada_file_manager.data_files[
            0
        ].intent
        self._pst_metadata.context.notes = self.dada_file_manager.data_files[
            0
        ].notes

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
            total_data_size += self.dada_file_manager.data_files[
                index
            ].file_size
            total_weights_size += self.dada_file_manager.weights_files[
                index
            ].file_size

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
        """Convert datetime UTC format to MJD"""
        date_object = datetime.strptime(utc_datetime, datetime_format)

        # Calculate Julian Date (including fractional part)
        days_since_2000_01_01 = (
            date_object - datetime(2000, 1, 1)
        ).total_seconds() / (24 * 3600)
        jd = days_since_2000_01_01 + 2451544.5

        # Calculate Modified Julian Date (MJD)
        mjd = jd - 2400000.5

        # Round to the desired accuracy
        rounded_mjd = round(mjd, 10)

        return str(Decimal(rounded_mjd))

    def build_obscore(self: MetaDataBuilder) -> None:
        """Build PstObsCore used for obscore block in metadata file."""

        # Grab fields from header file
        utc_start = self.dada_file_manager.data_files[0].utc_start
        scan_id = self.dada_file_manager.data_files[0].scan_id
        tsamp = float(self.dada_file_manager.data_files[0].tsamp)
        npol = int(self.dada_file_manager.data_files[0].npol)
        nchan = int(self.dada_file_manager.data_files[0].nchan)
        freq = float(self.dada_file_manager.data_files[0].freq)
        bw = float(self.dada_file_manager.data_files[0].bw)
        stt_crd1 = self.dada_file_manager.data_files[0].stt_crd1
        stt_crd2 = self.dada_file_manager.data_files[0].stt_crd2

        # Populate metadata field from hardcoded defaults
        dataproduct_type = OBSCORE_DATAPRODUCT_TYPE
        dataproduct_subtype = OBSCORE_DATAPRODUCT_SUBTYPE
        calib_level = OBSCORE_CALIB_LEVEL

        # Populate metadata fields using the header
        obs_id = scan_id
        target_name = self.dada_file_manager.data_files[0].source

        from astropy import units as u
        from astropy.coordinates import Angle, SkyCoord

        angle = Angle(stt_crd2, unit="degree")

        # Convert the Angle to the sexagesimal format
        sexagesimal_format = angle.to_string(unit="hourangle", sep=":")
        sky_coord = SkyCoord(
            f"{stt_crd1} {sexagesimal_format}",
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
        datetime_with_seconds_added = datetime_t_min + timedelta(
            seconds=seconds_to_add
        )
        utc_format = "%Y-%m-%d-%H:%M:%S.%f"
        t_max = self.convert_utc_to_mjd(
            datetime_with_seconds_added.strftime(utc_format), utc_format
        )

        # Convert microseconds to seconds
        t_resolution = float(tsamp) / 1000000.0

        # This is effectively the observation length
        t_exptime = tsamp

        total_data_size = self._pst_metadata.files[0].size
        total_header_size = 0

        for index in range(0, len(self.dada_file_manager.data_files)):
            total_header_size += self.dada_file_manager.data_files[
                index
            ].header_size

        access_estsize = total_data_size - total_header_size

        facility_name = OBSCORE_FACILITY_NAME
        instrument_name = OBSCORE_INSTRUMENT_NAME

        pol_xel = npol

        # Polarisations are not detected, expect a value of X, Y
        # best not to define it (keep it as null)
        pol_states = "null"

        em_xel = nchan
        em_unit = "Hz"

        em_min = (freq - (bw / 2)) * 1e6
        print(f"em_min {em_min}")
        em_max = (freq + (bw / 2)) * 1e6

        # TBC: Not sure what this quantity really means, sky resolution.
        em_res_power = "null"

        # TODO: Computed as (BW / NCHAN) * 1e6.
        # Value of Resolution along the spectral axis".
        # Not sure about overampling here...
        em_resolution = (bw / nchan) * 1e6

        # Unified Content Descriptor of observable,
        # not really anything suitable for PST.
        # Guessing this should be voltage ? put null for now.
        o_ucd = "null"

        obscore = PstObsCore(
            dataproduct_type=dataproduct_type,
            dataproduct_subtype=dataproduct_subtype,
            calib_level=calib_level,
            obs_id=obs_id,
            access_estsize=access_estsize,
            target_name=target_name,
            s_ra=s_ra,
            s_dec=s_dec,
            t_min=t_min,
            t_max=t_max,
            t_resolution=t_resolution,
            t_exptime=t_exptime,
            facility_name=facility_name,
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

    def write_metadata():
        print("MetaDataBuilder.write_metadata not implemented yet")

    @property
    def context(self: MetaDataBuilder) -> PstContext:
        return self._context

    @property
    def config(self: MetaDataBuilder) -> PstConfig:
        return self._config

    @property
    def dada_file_manager(self: MetaDataBuilder) -> DadaFileManager:
        return self._dada_file_manager

    @property
    def dsp_mount_path(self: MetaDataBuilder) -> str:
        return self._dsp_mount_path

    @dsp_mount_path.setter
    def dsp_mount_path(self: MetaDataBuilder, path: str) -> None:
        self._dsp_mount_path = path
        if self._dada_file_manager:
            self._dada_file_manager.set_dsp_mount_path(path)

    @property
    def pst_metadata(self: MetaDataBuilder) -> PstMetadata:
        return self._pst_metadata
