#!/usr/bin/env python3
"""
Pure Python FIT file converter.

This module provides direct binary manipulation of FIT files to change manufacturer ID.
"""

import struct
import logging
import os
from typing import Optional

def calculate_crc16(data):
    """Calculate CRC-16 for FIT file format"""
    crc_table = [
        0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
        0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400
    ]

    crc = 0
    for byte in data:
        tmp = crc_table[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ crc_table[byte & 0xF]

        tmp = crc_table[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ crc_table[(byte >> 4) & 0xF]

    return crc

# Configure logging
logger = logging.getLogger(__name__)


class FitConverterError(Exception):
    """Exception raised by FIT converter operations."""
    pass


class FitConverter:
    """Pure Python FIT file converter using binary manipulation."""

    def __init__(self):
        """Initialize the FIT converter."""
        pass

    def convert_fit(self, fit_data: bytes, debug_output: bool = True) -> bytes:
        """
        Convert FIT file by directly manipulating binary data.

        Args:
            fit_data: The original FIT file data as bytes
            debug_output: If True, save original and modified files for debugging

        Returns:
            Modified FIT file data as bytes

        Raises:
            FitConverterError: If the operation fails
        """
        if not isinstance(fit_data, bytes):
            raise FitConverterError("fit_data must be bytes")

        if not fit_data:
            raise FitConverterError("fit_data cannot be empty")

        try:
            modified_data = self._modify_manufacturer_binary(fit_data, 260)  # Zwift

            return modified_data
        except Exception as e:
            logger.error(f"Failed to convert FIT file: {e}")
            raise FitConverterError(f"Failed to convert FIT file: {e}")

    def _modify_manufacturer_binary(self, fit_data: bytes, new_manufacturer: int = 1) -> bytes:
        """
        Modify manufacturer and product IDs in FIT file using direct binary manipulation.

        This method processes file_id and device_info messages to set:
        - manufacturer to 1 (Garmin)
        - product to 3122 (Edge830)
        - Also adds FileCreator message for better compatibility

        Args:
            fit_data: Original FIT file data
            new_manufacturer: New manufacturer ID (default: 1 for Garmin)

        Returns:
            Modified FIT file data
        """
        # Make a mutable copy
        data = bytearray(fit_data)

        # Validate FIT file header
        if len(data) < 14:
            raise FitConverterError("Invalid FIT file: too short")

        # Check FIT signature
        if data[8:12] != b'.FIT':
            raise FitConverterError("Invalid FIT file: missing .FIT signature")

        # Get header size
        header_size = data[0]
        if header_size < 12:
            raise FitConverterError("Invalid FIT file: header too short")

        # Get data size from header
        data_size = struct.unpack('<I', data[4:8])[0]  # Little endian uint32

        logger.info(f"FIT file analysis: header_size={header_size}, data_size={data_size}, total_size={len(data)}")

        # Update FIT header to use Garmin compatible versions
        protocol_version = data[1]
        profile_version = struct.unpack('<H', data[2:4])[0]

        if protocol_version != 16:  # 1.0 protocol version
            logger.info(f"Updating protocol version from {protocol_version} to 16")
            data[1] = 16

        if profile_version != 2134:  # Typical Garmin profile version
            logger.info(f"Updating profile version from {profile_version} to 2134")
            struct.pack_into('<H', data, 2, 2134)

        # Print first 32 bytes for debugging
        hex_dump = ' '.join(f'{b:02x}' for b in data[:32])
        logger.info(f"First 32 bytes: {hex_dump}")        # Start parsing messages after header
        pos = header_size
        end_pos = min(header_size + data_size, len(data) - 2)  # Exclude CRC

        # Store definition messages for later use
        # Track message types
        local_definitions = {}
        manufacturer_changed = False
        file_creator_found = False

        # Look for file_id message (Global Message Number 0)
        while pos < end_pos and pos < len(data):
            if pos >= len(data):
                break

            header_byte = data[pos]
            pos += 1

            logger.debug(f"Processing message at pos {pos-1}: header_byte=0x{header_byte:02x}")

            # Check if this is a definition message
            # Normal header: bit 7 = 0, bit 6 = 1 for definition message
            # Compressed header: bit 7 = 1 (time stamp, not definition)
            if (header_byte & 0x80) == 0 and (header_byte & 0x40) != 0:
                # Definition message
                local_msg_type = header_byte & 0x0F

                if pos + 4 >= len(data):
                    logger.warning("Not enough data for definition message")
                    break

                reserved = data[pos]
                architecture = data[pos + 1]
                global_msg_num = struct.unpack('<H', data[pos + 2:pos + 4])[0]
                pos += 4

                if pos >= len(data):
                    break

                num_fields = data[pos]
                pos += 1

                logger.debug(f"Definition message: local_type={local_msg_type}, global_msg={global_msg_num}, num_fields={num_fields}")

                # Store field definitions
                fields = []
                for i in range(num_fields):
                    if pos + 3 > len(data):
                        break
                    field_def_num = data[pos]
                    field_size = data[pos + 1]
                    field_type = data[pos + 2]
                    fields.append((field_def_num, field_size, field_type))
                    pos += 3

                # Store definition for this local message type
                local_definitions[local_msg_type] = {
                    'global_msg_num': global_msg_num,
                    'fields': fields
                }

                logger.debug(f"Stored definition for local type {local_msg_type}: global_msg={global_msg_num}")

                # Log if this is a file_id or device_info definition
                if global_msg_num == 0:
                    logger.info(f"Found file_id message definition (local type {local_msg_type})")
                elif global_msg_num == 23:
                    logger.info(f"Found device_info message definition (local type {local_msg_type})")
                elif global_msg_num == 49:
                    logger.info(f"Found existing file_creator message definition (local type {local_msg_type})")
                    file_creator_found = True

            else:
                # Normal data record (bit 7 = 0)
                local_msg_type = header_byte & 0x0F

                logger.debug(f"Data message: local_type={local_msg_type}")

                # Check if this is file_id or device_info message
                if local_msg_type in local_definitions:
                    definition = local_definitions[local_msg_type]

                    if definition['global_msg_num'] == 0:  # file_id message
                        logger.info(f"Found file_id message at position {pos-1} (0x{pos-1:04x})")

                        # Show hex dump of this message for verification
                        message_size = sum(field[1] for field in definition['fields'])
                        hex_data = ' '.join(f'{data[pos+i]:02x}' for i in range(min(message_size, 16)))
                        logger.info(f"Message data (first 16 bytes): {hex_data}")

                        # Process file_id message fields
                        field_offset = 0
                        for field_def_num, field_size, field_type in definition['fields']:
                            if pos + field_offset + field_size > len(data):
                                break

                            logger.debug(f"Field {field_def_num}: size={field_size}, type={field_type}, offset={field_offset}")

                            # Field 0 is type in file_id message
                            if field_def_num == 0 and field_size == 1:
                                current_type = data[pos + field_offset]
                                logger.info(f"Found type field in file_id: current={current_type}, changing to 4 (activity)")

                                # Set type to activity (4)
                                data[pos + field_offset] = 4
                                logger.info(f"Successfully changed file_id type from {current_type} to 4 (activity)")

                            # Field 1 is manufacturer in file_id message
                            elif field_def_num == 1 and field_size == 2:
                                current_manufacturer = struct.unpack('<H', data[pos + field_offset:pos + field_offset + 2])[0]
                                logger.info(f"Found manufacturer field in file_id: current={current_manufacturer}, changing to 1 (Garmin)")

                                # Set manufacturer to Garmin (1)
                                struct.pack_into('<H', data, pos + field_offset, 1)
                                logger.info(f"Successfully changed manufacturer from {current_manufacturer} to 1 (Garmin)")
                                manufacturer_changed = True

                            # Field 2 is product in file_id message
                            elif field_def_num == 2 and field_size == 2:
                                current_product = struct.unpack('<H', data[pos + field_offset:pos + field_offset + 2])[0]
                                logger.info(f"Found product field in file_id: current={current_product}, changing to 3122 (Edge830)")

                                # Set product to Edge 830 (3122)
                                struct.pack_into('<H', data, pos + field_offset, 3122)
                                logger.info(f"Successfully changed product from {current_product} to 3122 (Edge830)")

                            # Field 4 is time_created in file_id message
                            elif field_def_num == 4 and field_size == 4:
                                current_time = struct.unpack('<I', data[pos + field_offset:pos + field_offset + 4])[0]
                                # Convert to human readable for logging
                                import datetime
                                fit_epoch = datetime.datetime(1989, 12, 31, tzinfo=datetime.timezone.utc)
                                if current_time > 0:
                                    activity_time = fit_epoch + datetime.timedelta(seconds=current_time)
                                    logger.info(f"Activity timestamp: {activity_time.isoformat()}")
                                else:
                                    logger.info("No timestamp found in file_id, keeping current value")

                            field_offset += field_size

                        # Skip to next message
                        pos += sum(field[1] for field in definition['fields'])

                    elif definition['global_msg_num'] == 23:  # device_info message
                        logger.info(f"Found device_info message at position {pos-1}")

                        # Process device_info message fields
                        field_offset = 0
                        for field_def_num, field_size, field_type in definition['fields']:
                            if pos + field_offset + field_size > len(data):
                                break

                            logger.debug(f"Device info field {field_def_num}: size={field_size}, type={field_type}, offset={field_offset}")

                            # Field 2 is manufacturer in device_info message
                            if field_def_num == 2 and field_size == 2:
                                current_manufacturer = struct.unpack('<H', data[pos + field_offset:pos + field_offset + 2])[0]
                                logger.info(f"Found manufacturer field in device_info: current={current_manufacturer}, changing to 1 (Garmin)")

                                # Set manufacturer to Garmin (1)
                                struct.pack_into('<H', data, pos + field_offset, 1)
                                logger.info(f"Successfully changed device_info manufacturer from {current_manufacturer} to 1 (Garmin)")
                                manufacturer_changed = True

                            # Field 4 is product in device_info message
                            elif field_def_num == 4 and field_size == 2:
                                current_product = struct.unpack('<H', data[pos + field_offset:pos + field_offset + 2])[0]
                                logger.info(f"Found product field in device_info: current={current_product}, changing to 3122 (Edge830)")

                                # Set product to Edge 830 (3122)
                                struct.pack_into('<H', data, pos + field_offset, 3122)
                                logger.info(f"Successfully changed device_info product from {current_product} to 3122 (Edge830)")

                            field_offset += field_size

                        # Skip to next message
                        pos += sum(field[1] for field in definition['fields'])
                    else:
                        # Skip this data message
                        pos += sum(field[1] for field in definition['fields'])
                else:
                    logger.debug(f"No definition found for local message type {local_msg_type} at position {pos-1} (0x{pos-1:04x})")
                    # If we don't have the definition, we can't proceed safely
                    # This suggests our message parsing has gone off track
                    logger.warning(f"Message parsing may be corrupted at position {pos-1}, stopping to avoid further corruption")
                    break

        if manufacturer_changed:
            logger.info("FIT file manufacturer and product fields successfully modified")

            # Add FileCreator message only if not already present
            if not file_creator_found:
                logger.info("Adding FileCreator message for Garmin compatibility")
                file_creator_data = self._create_file_creator_message()

                # Insert FileCreator message before the CRC (last 2 bytes)
                insert_pos = len(data) - 2
                data[insert_pos:insert_pos] = file_creator_data

                # Update data size in header
                new_data_size = data_size + len(file_creator_data)
                struct.pack_into('<I', data, 4, new_data_size)
                logger.info(f"Updated data size from {data_size} to {new_data_size}")
            else:
                logger.info("FileCreator message already exists, skipping addition")

            # Recalculate and update CRC
            logger.info("Recalculating FIT file CRC...")
            if len(data) >= 16:
                # Calculate CRC for the entire file except the last 2 bytes (CRC itself)
                crc_data = data[:-2]
                new_crc = calculate_crc16(crc_data)

                # Update CRC at the end of file
                struct.pack_into('<H', data, len(data) - 2, new_crc)
                logger.info(f"Updated FIT file CRC to: {new_crc:04X}")

            return bytes(data)
        else:
            logger.warning("No file_id or device_info messages found or manufacturer/product fields not modified")
            return bytes(data)

    def _create_file_creator_message(self) -> bytearray:
        """Create FileCreator message for Garmin compatibility."""
        message_data = bytearray()

        # FileCreator definition message (global message 49)
        # Definition message header: 0x40 | local_msg_type (7)
        message_data.append(0x40 | 7)  # Definition message, local type 7
        message_data.append(0x00)      # Reserved
        message_data.append(0x00)      # Architecture (little endian)
        message_data.append(0x31)      # Global message number (49) - low byte
        message_data.append(0x00)      # Global message number (49) - high byte
        message_data.append(0x02)      # Number of fields

        # Field definitions for FileCreator
        # Field 0: software_version (2 bytes)
        message_data.extend([0x00, 0x02, 0x84])  # field_def_num=0, size=2, base_type=132 (uint16)
        # Field 1: hardware_version (1 byte)
        message_data.extend([0x01, 0x01, 0x02])  # field_def_num=1, size=1, base_type=2 (uint8)

        # FileCreator data message
        message_data.append(0x07)  # Data message, local type 7
        message_data.extend(struct.pack('<H', 975))   # software_version = 975 (Edge 520 firmware version)
        message_data.append(255)   # hardware_version = 255

        logger.info(f"Created FileCreator message ({len(message_data)} bytes)")
        return message_data

# Convenience function for direct use
def convert_fit(fit_data: bytes, debug_output: bool = True) -> bytes:
    """
    Convenience function to convert FIT file.

    Args:
        fit_data: The original FIT file data as bytes
        debug_output: If True, save debug files

    Returns:
        Converted FIT file data as bytes
    """
    converter = FitConverter()
    return converter.convert_fit(fit_data, debug_output)
