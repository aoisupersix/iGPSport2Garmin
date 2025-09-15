"""
FIT Converter - Pure Python FIT file manipulation library.

This package provides functions to modify FIT files using direct binary manipulation,
particularly for changing manufacturer IDs to enable training status features in Garmin Connect.
"""

from .fit_converter import (
    FitConverter,
    FitConverterError,
    convert_fit
)

__version__ = "1.0.0"
__all__ = [
    "FitConverter",
    "FitConverterError",
    "convert_fit"
]
