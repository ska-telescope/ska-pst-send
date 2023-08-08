# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST Testutils project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for structure used for writing YAML meta data files."""
from __future__ import annotations

from typing import Any, Dict, List

import yaml

__all__ = [
    "PstContext",
    "PstConfig",
    "PstFiles",
    "PstObsCore",
    "PstMetadata",
]


class PstContext:
    def __init__(
        self: PstContext,
        observer: str = "",
        intent: str = "",
        notes: str = "",
    ) -> None:
        self._observer = observer
        self._intent = intent
        self._notes = notes

    def to_dict(self: PstContext) -> Dict[str, str]:
        return {
            "observer": self._observer,
            "intent": self._intent,
            "notes": self._notes,
        }

    @property
    def observer(self: PstContext) -> str:
        return self._observer

    @observer.setter
    def observer(self: PstContext, observer: str) -> None:
        self._observer = observer

    @property
    def intent(self: PstContext) -> str:
        return self._intent

    @intent.setter
    def intent(self: PstContext, intent: str) -> None:
        self._intent = intent

    @property
    def notes(self: PstContext) -> str:
        return self._notes

    @notes.setter
    def notes(self: PstContext, notes: str) -> None:
        self._notes = notes


class PstConfig:
    def __init__(
        self: PstConfig,
        image: str = "",
        version: str = "",
    ) -> None:
        """"""
        self._image = image
        self._version = version

    def to_dict(self: PstContext) -> Dict[str, str]:
        return {
            "image": self._image,
            "version": self._version,
        }

    @property
    def image(self: PstConfig) -> str:
        return self._image

    @image.setter
    def image(self: PstConfig, image: str) -> None:
        self._image = image

    @property
    def version(self: PstConfig) -> str:
        return self._version

    @version.setter
    def version(self: PstConfig, version: str) -> None:
        self._version = version


class PstFiles:
    def __init__(
        self: PstFiles,
        description: str = "",
        path: str = "",
        size: str = "",
        status: str = "done",
    ):
        self._description = description
        self._path = path
        self._size = size
        self._status = status

    def to_dict(self: PstFiles) -> Dict[str, str]:
        return {
            "description": self._description,
            "path": self._path,
            "size": self._size,
            "status": self._status,
        }

    @property
    def description(self):
        return self._description

    @property
    def path(self):
        return self._path

    @property
    def size(self):
        return self._size

    @property
    def status(self):
        return self._status


class PstObsCore:
    def __init__(
        self: PstObsCore,
        dataproduct_type: str = "",
        dataproduct_subtype: str = "",
        calib_level="",
        obs_id: str = "",
        access_estsize: str = "",
        target_name: str = "",
        s_ra: str = "",
        s_dec: str = "",
        t_min: str = "",
        t_max: str = "",
        t_resolution: str = "",
        t_exptime: str = "",
        facility_name: str = "",
        instrument_name: str = "",
        pol_xel: str = "",
        pol_states: str = "",
        em_xel: str = "",
        em_unit: str = "",
        em_min: str = "",
        em_max: str = "",
        em_res_power: str = "",
        em_resolution: str = "",
        o_ucd: str = "",
    ):
        self._dataproduct_type = dataproduct_type
        self._dataproduct_subtype = dataproduct_subtype
        self._calib_level = calib_level
        self._obs_id = obs_id
        self._access_estsize = access_estsize
        self._target_name = target_name
        self._s_ra = s_ra
        self._s_dec = s_dec
        self._t_min = t_min
        self._t_max = t_max
        self._t_resolution = t_resolution
        self._t_exptime = t_exptime
        self._facility_name = facility_name
        self._instrument_name = instrument_name
        self._pol_xel = pol_xel
        self._pol_states = pol_states
        self._em_xel = em_xel
        self._em_unit = em_unit
        self._em_min = em_min
        self._em_max = em_max
        self._em_res_power = em_res_power
        self._em_resolution = em_resolution
        self._o_ucd = o_ucd

    def to_dict(self: PstObsCore) -> Dict[str, str]:
        return {
            "dataproduct_type": self._dataproduct_type,
            "dataproduct_subtype": self._dataproduct_subtype,
            "calib_level": self._calib_level,
            "obs_id": self._obs_id,
            "access_estsize": self._access_estsize,
            "target_name": self._target_name,
            "s_ra": self._s_ra,
            "s_dec": self._s_dec,
            "t_min": self._t_min,
            "t_max": self._t_max,
            "t_resolution": self._t_resolution,
            "t_exptime": self._t_exptime,
            "facility_name": self._facility_name,
            "instrument_name": self._instrument_name,
            "pol_xel": self._pol_xel,
            "pol_states": self._pol_states,
            "em_xel": self._em_xel,
            "em_unit": self._em_unit,
            "em_min": self._em_min,
            "em_max": self._em_max,
            "em_res_power": self._em_res_power,
            "em_resolution": self._em_resolution,
            "o_ucd": self._o_ucd,
        }

    @property
    def dataproduct_type(self):
        return self._dataproduct_type

    @property
    def dataproduct_subtype(self):
        return self._dataproduct_subtype

    @property
    def calib_level(self):
        return self._calib_level

    @property
    def obs_id(self):
        return self._obs_id

    @property
    def access_estsize(self):
        return self._access_estsize

    @property
    def target_name(self):
        return self._target_name

    @property
    def s_ra(self):
        return self._s_ra

    @property
    def s_dec(self):
        return self._s_dec

    @property
    def t_min(self):
        return self._t_min

    @property
    def t_max(self):
        return self._t_max

    @property
    def t_resolution(self):
        return self._t_resolution

    @property
    def t_exptime(self):
        return self._t_exptime

    @property
    def facility_name(self):
        return self._facility_name

    @property
    def instrument_name(self):
        return self._instrument_name

    @property
    def pol_xel(self):
        return self._pol_xel

    @property
    def pol_states(self):
        return self._pol_states

    @property
    def em_xel(self):
        return self._em_xel

    @property
    def em_unit(self):
        return self._em_unit

    @property
    def em_min(self):
        return self._em_min

    @property
    def em_max(self):
        return self._em_max

    @property
    def em_res_power(self):
        return self._em_res_power

    @property
    def em_resolution(self):
        return self._em_resolution

    @property
    def o_ucd(self):
        return self._o_ucd


class PstMetadata:
    def __init__(
        self: PstMetadata,
        interface: str = "",
        execution_block: str = "",
        context=PstContext,
        config=PstConfig,
        obscore=PstObsCore,
    ) -> None:
        self._interface = interface
        self._execution_block = execution_block
        self._context = context
        self._config = config
        self._files = [
            PstFiles(
                description="Channelised voltage data raw files",
                path="data",
                size="",
                status="done",
            ),
            PstFiles(
                description="Channelised weights data raw files",
                path="weights",
                size="",
                status="done",
            ),
        ]
        self._obscore = obscore

    # Properties with setters
    @property
    def interface(self) -> str:
        return self._interface

    @interface.setter
    def interface(self, value: str) -> None:
        self._interface = str(value)

    @property
    def execution_block(self) -> str:
        return self._execution_block

    @execution_block.setter
    def execution_block(self, value: str) -> None:
        self._execution_block = str(value)

    @property
    def context(self) -> PstContext:
        return self._context

    @context.setter
    def context(self, value: PstContext) -> None:
        self._context = value

    @property
    def config(self) -> PstConfig:
        return self._config

    @config.setter
    def config(self, value: PstConfig) -> None:
        self._config = value

    @property
    def files(self) -> List[PstFiles]:
        return self._files

    @files.setter
    def files(self, value: List[PstFiles]) -> None:
        if not isinstance(value, list):
            raise ValueError("Files must be a list.")
        for item in value:
            if not isinstance(item, PstFiles):
                raise ValueError(
                    "Each element of files must be an instance of PstFiles."
                )
        self._files = value

    @property
    def obscore(self) -> PstObsCore:
        return self._obscore

    @obscore.setter
    def obscore(self, value: PstObsCore) -> None:
        if not isinstance(value, PstObsCore):
            raise ValueError("Obscore must be an instance of PstObsCore.")
        self._obscore = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interface": self.interface,
            "execution_block": self.execution_block,
            "context": self.context.to_dict(),
            "config": self.config.to_dict(),
            "files": [file.to_dict() for file in self.files],
            "obscore": self.obscore.to_dict(),
        }

    def to_yaml(self) -> str:
        metadata_dict = self.to_dict()
        return yaml.dump(metadata_dict)

    @property
    def yaml_object(self) -> yaml.YAMLObject:
        metadata_dict = self.metadata_to_dict()
        return yaml.load(yaml.dump(metadata_dict), Loader=yaml.SafeLoader)
