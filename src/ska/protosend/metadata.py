# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST Testutils project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for structure used for writing YAML meta data files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import yaml

__all__ = [
    "PstContext",
    "PstConfig",
    "PstFiles",
    "PstObsCore",
    "PstMetaData",
]


@dataclass
class PstContext:
    """
    A data class to represent the context field of a pst metadata file.

    context is meant to be data passed verbatim through from OET/TMC as part of AssignResources (SDP)
    or Configure (other sub-systems). To be made part of ska_telmodel schemas.

    :ivar observer: Name or role of the person conducting the observation
    :vartype observer: str
    :ivar intent: intent passed from OET/TMC
    :vartype intent: str
    :ivar notes: notes passed from OET/TMC
    :vartype notes: str
    """

    observer: str = field(default="")
    intent: str = field(default="Tied-array beam observation")
    notes: str = field(default="")

    def to_dict(self: PstContext) -> Dict[str, str]:
        """Get the object properties in dict format."""
        return {
            "observer": self.observer,
            "intent": self.intent,
            "notes": self.notes,
        }


@dataclass
class PstConfig:
    """
    A data class to represent the config field of a pst metadata file.

    Configuration of generating software.

    :ivar image: chart name
    :vartype image: str
    :ivar version: chart version
    :vartype version: str
    """

    image: str = field(default="")
    version: str = field(default="")

    def to_dict(self: PstConfig) -> Dict[str, str]:
        """Get the object properties in dict format."""
        return {
            "image": self.image,
            "version": self.version,
        }


@dataclass
class PstFiles:
    """
    A data class to represent the files field of a pst metadata file.

    Documentation concerning files coupled to the pst metadata file.

    :ivar description:
    :vartype description: str
    :ivar path:
    :vartype path: str
    :ivar size:
    :vartype size: str
    :ivar status:
    :vartype status: str
    """

    description: str = field(default="")
    path: str = field(default="")
    size: str = field(default="")
    status: str = field(default="done")

    def to_dict(self: PstFiles) -> Dict[str, str]:
        """Get the object properties in dict format."""
        return {
            "description": self.description,
            "path": self.path,
            "size": self.size,
            "status": self.status,
        }


@dataclass
class PstObsCore:
    """
    A dataclass to definition of the standard IVOA ObsCore table/view.

    :ivar dataproduct_type: Logical data product type, such as image, cube, spectrum, sed,
                            timeseries, visibility, event or measurements
    :vartype dataproduct_type: str
    :ivar dataproduct_subtype: voltages, oversampled, channelised, quantised voltages
    :vartype dataproduct_subtype: str
    :ivar calib_level: Calibration level (0, 1, 2, 3, 4)
                       0 = Raw instrumental data
                       1 = Instrumental data in a standard format (FITS, VOTable, SDFITS, ASDM, etc.)
                       2 = Calibrated, science ready data with the instrument signature removed
                       3 = Enhanced data products like mosaics, resampled or drizzled images,
                       or heavily processed survey fields
                       4 = Analysis data products generated after some scientific data manipulation or
                       interpretation.
    :vartype calib_level: str
    :ivar obs_id: scan id
    :vartype obs_id: str
    :ivar access_estsize: value derived from the recorded data files upon stop_scan()
    :vartype access_estsize: str
    :ivar target_name: Astronomical object observed
    :vartype target_name: str
    :ivar s_ra: Centre of observation right ascension, ICRS
    :vartype s_ra: str
    :ivar s_dec: Centre of observation declination, ICRS
    :vartype s_dec: str
    :ivar t_min: Start time in MJD
    :vartype t_min: str
    :ivar t_max: Stop time in MJD
    :vartype t_max: str
    :ivar t_resolution: Temporal resolution FWHM (full width at half maximum)
    :vartype t_resolution: str
    :ivar t_exptime: Total exposure time.
    :vartype t_exptime: str
    :ivar facility_name: The observatory or facility used to collect the data
    :vartype facility_name: str
    :ivar instrument_name: The name of the instrument used for the acquisition of the observation
    :vartype instrument_name: str
    :ivar pol_xel: Number of polarization samples
    :vartype pol_xel: str
    :ivar pol_states: List of polarization states
    :vartype pol_states: str
    :ivar em_xel: Number of elements along the spectral axis
    :vartype em_xel: str
    :ivar em_unit: Spectral coordinates unit type. Defaults to Hz.
    :vartype em_unit: str
    :ivar em_min: Start in spectral coordinates (vacuum wavelength)
    :vartype em_min: str
    :ivar em_max: Stop in spectral coordinates (vacuum wavelength)
    :vartype em_max: str
    :ivar em_res_power: Spectral resolving power
    :vartype em_res_power: str
    :ivar em_resolution: Spectral resolution
    :vartype em_resolution: str
    :ivar o_ucd: Unified Content Descriptor of observable e.g. phot.count or phot.flux.density
                 see section 4.18 and B.6.4.1 in Obscore standard,
                 UCD1+ controlled vocabulary and especially list of observables),
                 not really anything suitable for PST.
    :vartype o_ucd: str
    """

    dataproduct_type: str = field(default="timeseries")
    dataproduct_subtype: str = field(default="voltages")
    calib_level: str = field(default="0")
    obs_id: str = field(default="")
    access_estsize: str = field(default="")
    target_name: str = field(default="")
    s_ra: str = field(default="")
    s_dec: str = field(default="")
    t_min: str = field(default="")
    t_max: str = field(default="")
    t_resolution: str = field(default="")
    t_exptime: str = field(default="")
    facility_name: str = field(default="SKA-Observatory")
    instrument_name: str = field(default="")
    pol_xel: str = field(default="")
    pol_states: str = field(default="")
    em_xel: str = field(default="")
    em_unit: str = field(default="Hz")
    em_min: str = field(default="")
    em_max: str = field(default="")
    em_res_power: str = field(default="")
    em_resolution: str = field(default="")
    o_ucd: str = field(default="null")

    def to_dict(self: PstObsCore) -> Dict[str, str]:
        """Get the object properties in dict format."""
        return {
            "dataproduct_type": self.dataproduct_type,
            "dataproduct_subtype": self.dataproduct_subtype,
            "calib_level": self.calib_level,
            "obs_id": self.obs_id,
            "access_estsize": self.access_estsize,
            "target_name": self.target_name,
            "s_ra": self.s_ra,
            "s_dec": self.s_dec,
            "t_min": self.t_min,
            "t_max": self.t_max,
            "t_resolution": self.t_resolution,
            "t_exptime": self.t_exptime,
            "facility_name": self.facility_name,
            "instrument_name": self.instrument_name,
            "pol_xel": self.pol_xel,
            "pol_states": self.pol_states,
            "em_xel": self.em_xel,
            "em_unit": self.em_unit,
            "em_min": self.em_min,
            "em_max": self.em_max,
            "em_res_power": self.em_res_power,
            "em_resolution": self.em_resolution,
            "o_ucd": self.o_ucd,
        }


@dataclass
class PstMetaData:
    """Class representing the PST metadata.

    This class encapsulates the metadata information for a PST (Processing Science Target)
    data product. It includes details about the interface, execution block, context,
    configuration, files, and observation core information.

    :ivar interface: The interface of the metadata.
    :vartype interface: str

    :ivar execution_block: The execution block identifier.
    :vartype execution_block: str

    :ivar context: The context information for the PST data.
    :vartype context: PstContext

    :ivar config: The configuration information for the PST data.
    :vartype config: PstConfig

    :ivar files: List of files associated with the PST data.
    :vartype files: List[PstFiles]

    :ivar obscore: The observation core information for the PST data.
    :vartype obscore: PstObsCore
    """

    interface: str = field(default="")
    execution_block: str = field(default="")
    context: PstContext = field(default_factory=PstContext)
    config: PstConfig = field(default_factory=PstConfig)
    files: List[PstFiles] = field(default_factory=list)
    obscore: PstObsCore = field(default_factory=PstObsCore)

    def to_dict(self: PstMetaData) -> Dict[str, Any]:
        """Get the object properties in dict format."""
        return {
            "interface": self.interface,
            "execution_block": self.execution_block,
            "context": self.context.to_dict(),
            "config": self.config.to_dict(),
            "files": [file.to_dict() for file in self.files],
            "obscore": self.obscore.to_dict(),
        }

    def to_yaml(self: PstMetaData) -> str:
        """Get the object properties in yaml representation in string format."""
        metadata_dict = self.to_dict()
        return yaml.dump(metadata_dict)

    @property
    def yaml_object(self: PstMetaData) -> yaml.YAMLObject:
        """Get the object properties as a yaml object."""
        metadata_dict = self.to_dict()
        return yaml.load(yaml.dump(metadata_dict), Loader=yaml.SafeLoader)
