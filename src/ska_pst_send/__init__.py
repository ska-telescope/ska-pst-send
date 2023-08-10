# -*- coding: utf-8 -*-

"""Module init code."""


__version__ = "0.0.0"

__author__ = ["Jesmigel A. Cantos"]
__email__ = ["jesmigel.developer@gmail.com"]

import logging

from .metadata_builder import MetaDataBuilder

logger = logging.getLogger("ska_pst_send")

logger.info(f"{MetaDataBuilder()}")
