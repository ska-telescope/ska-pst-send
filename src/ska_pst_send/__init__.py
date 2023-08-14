# -*- coding: utf-8 -*-

"""Module init code."""


__version__ = "0.0.0"

__author__ = ["Jesmigel A. Cantos"]
__email__ = ["jesmigel.developer@gmail.com"]

import logging

from .metadata_builder import MetaDataBuilder
from .scan_manager import ScanManager
from .scan_process import ScanProcess
from .scan_transfer import ScanTransfer

logger = logging.getLogger("ska_pst_send")

logger.info(f"{MetaDataBuilder()}")
