# -*- coding: utf-8 -*-

"""Module init code."""


__version__ = "0.0.0"

__author__ = ["Jesmigel A. Cantos"]
__email__ = ["jesmigel.developer@gmail.com"]

import logging

from .metadata_builder import MetaDataBuilder
from .scan import Scan
from .scan_manager import ScanManager
from .scan_transfer import ScanTransfer
from .scan_process import ScanProcess
from .sdp_transfer import SdpTransfer
from .voltage_recorder_scan import VoltageRecorderScan
from .voltage_recorder_file import VoltageRecorderFile

__all__ = [
    "Scan",
    "ScanManager",
    "ScanTransfer",
    "ScanProcess",
    "VoltageRecorderScan",
    "VoltageRecorderFile",
    "SdpTransfer",
]

logger = logging.getLogger("ska_pst_send")

logger.info(f"{MetaDataBuilder()}")
