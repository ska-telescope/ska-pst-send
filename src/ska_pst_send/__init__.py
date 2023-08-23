# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module init code."""
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
