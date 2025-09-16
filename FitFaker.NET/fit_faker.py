#!/usr/bin/env python3
"""
Python wrapper for FitFaker.NET using pythonnet.

This script provides a Python interface to the FitFaker.NET library
for modifying FIT files using the official Garmin FIT SDK.
"""

import sys
import os
import tempfile
from pathlib import Path
from typing import Optional

# Set .NET Core runtime for pythonnet
os.environ["PYTHONNET_RUNTIME"] = "coreclr"

try:
    import clr
except ImportError:
    print("Error: pythonnet is not installed. Please install it with: pip install pythonnet")
    sys.exit(1)


class FitFaker:
    """Python wrapper for FitFaker.NET library."""

    def __init__(self):
        """Initialize the FitFaker with the .NET assembly."""
        # Add the .NET assembly to the Python runtime
        try:
            clr.AddReference("FitFaker.NET")
            print(f"Successfully loaded FitFaker.NET assembly")

            # Import the .NET namespace after loading the assembly
            from FitFaker.NET import Faker
            self._faker = Faker

        except Exception as e:
            raise RuntimeError(f"Failed to load FitFaker.NET assembly: {e}")

    def fake_from_bytes(self, fit_data: bytes) -> Optional[bytes]:
        """
        Modify a FIT file using FitFaker.NET from bytes data.

        Args:
            fit_data (bytes): FIT file content as bytes

        Returns:
            Optional[bytes]: Modified FIT file content as bytes, or None if failed
        """
        # Create temporary file for input
        with tempfile.NamedTemporaryFile(suffix='.fit', delete=False) as temp_input:
            temp_input.write(fit_data)
            temp_input_path = temp_input.name

        try:
            # Call FitFaker.NET to process the temporary file
            result = self._faker.Fake(temp_input_path)

            if result:
                # Read the modified file back as bytes
                with open(temp_input_path, 'rb') as f:
                    modified_data = f.read()
                print(f"Successfully processed FIT file ({len(fit_data)} -> {len(modified_data)} bytes)")
                return modified_data
            else:
                print("Failed to process FIT file with FitFaker.NET")
                return None

        except Exception as e:
            print(f"Exception occurred while processing FIT file: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_input_path)
            except OSError:
                pass

    def fake(self, fit_file_path: str) -> bool:
        """
        Modify a FIT file using FitFaker.NET.

        Args:
            fit_file_path (str): Path to the FIT file to modify

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(fit_file_path):
            print(f"Error: FIT file not found: {fit_file_path}")
            return False

        try:
            # Read the original file
            with open(fit_file_path, 'rb') as f:
                original_data = f.read()

            # Process using bytes method
            modified_data = self.fake_from_bytes(original_data)

            if modified_data is not None:
                # Write the modified data back to the original file
                with open(fit_file_path, 'wb') as f:
                    f.write(modified_data)
                print(f"Successfully processed FIT file: {fit_file_path}")
                return True
            else:
                print(f"Failed to process FIT file: {fit_file_path}")
                return False

        except Exception as e:
            print(f"Exception occurred while processing FIT file: {e}")
            return False
