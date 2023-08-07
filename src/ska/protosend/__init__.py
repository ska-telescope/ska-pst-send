# -*- coding: utf-8 -*-

"""Module init code."""


__version__ = "0.0.0"

__author__ = ["Jesmigel A. Cantos"]
__email__ = ["jesmigel.developer@gmail.com"]

import logging

from .example import SKA, function_example
from .metadata_builder import MetaDataBuilder

logger = logging.getLogger("ska-pst-protosend")

print(f"SKA.example: {SKA.example}")
print(f"function_example: {function_example}")
print(f"{MetaDataBuilder()}")
