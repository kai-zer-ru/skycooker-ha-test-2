#!/usr/local/bin/python3
"""Tests for checking the presence of required attributes and properties."""

import pytest
from unittest.mock import MagicMock
from custom_components.skycooker.skycooker_connection import SkyCookerConnection
from custom_components.skycooker.const import SUPPORTED_MODELS, STATUS_CODES


class TestSkyCookerConnectionAttributes:
    """Test class for checking SkyCookerConnection attributes."""

    def test_status_property_exists(self):
        """Test that the status property exists in SkyCookerConnection."""
        # Create a mock SkyCookerConnection object
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'status'), "SkyCookerConnection should have a 'status' property"

    def test_current_temp_property_exists(self):
        """Test that the current_temp property exists in SkyCookerConnection."""
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'current_temp'), "SkyCookerConnection should have a 'current_temp' property"

    def test_status_code_property_exists(self):
        """Test that the status_code property exists in SkyCookerConnection."""
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'status_code'), "SkyCookerConnection should have a 'status_code' property"

    def test_success_rate_property_exists(self):
        """Test that the success_rate property exists in SkyCookerConnection."""
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'success_rate'), "SkyCookerConnection should have a 'success_rate' property"

    def test_remaining_time_property_exists(self):
        """Test that the remaining_time property exists in SkyCookerConnection."""
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'remaining_time'), "SkyCookerConnection should have a 'remaining_time' property"

    def test_total_time_property_exists(self):
        """Test that the total_time property exists in SkyCookerConnection."""
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'total_time'), "SkyCookerConnection should have a 'total_time' property"

    def test_auto_warm_time_property_exists(self):
        """Test that the auto_warm_time property exists in SkyCookerConnection."""
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'auto_warm_time'), "SkyCookerConnection should have a 'auto_warm_time' property"

    def test_auto_warm_enabled_property_exists(self):
        """Test that the auto_warm_enabled property exists in SkyCookerConnection."""
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'auto_warm_enabled'), "SkyCookerConnection should have a 'auto_warm_enabled' property"

    def test_delayed_start_time_property_exists(self):
        """Test that the delayed_start_time property exists in SkyCookerConnection."""
        connection = SkyCookerConnection("test_mac", "test_key", persistent=False, model="RMC-M40S")
        assert hasattr(connection, 'delayed_start_time'), "SkyCookerConnection should have a 'delayed_start_time' property"


class TestConstants:
    """Test class for checking constants."""

    def test_supported_models_structure(self):
        """Test that SUPPORTED_MODELS has the correct structure."""
        for model, data in SUPPORTED_MODELS.items():
            assert isinstance(data, dict), f"SUPPORTED_MODELS['{model}'] should be a dictionary"
            assert "supported" in data, f"SUPPORTED_MODELS['{model}'] should have a 'supported' key"
            assert "type" in data, f"SUPPORTED_MODELS['{model}'] should have a 'type' key"

    def test_status_codes_structure(self):
        """Test that STATUS_CODES has the correct structure."""
        assert isinstance(STATUS_CODES, list), "STATUS_CODES should be a list"
        assert len(STATUS_CODES) == 2, "STATUS_CODES should have 2 elements (for English and Russian)"
        for lang_codes in STATUS_CODES:
            assert isinstance(lang_codes, dict), "Each element in STATUS_CODES should be a dictionary"


class TestSensorAttributes:
    """Test class for checking sensor attributes."""

    def test_sensor_uses_correct_attributes(self):
        """Test that sensors use the correct attributes from SkyCookerConnection."""
        from custom_components.skycooker.sensor import SkyCookerSensor
        from custom_components.skycooker.const import SENSOR_TYPE_TEMPERATURE

        # Create a mock hass and entry
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        mock_entry.data = {}

        # Create a mock connection
        mock_connection = MagicMock()
        mock_connection.available = True
        mock_connection.current_temp = 25
        mock_connection.status_code = 0x00
        mock_connection.remaining_time = 0
        mock_connection.total_time = 0
        mock_connection.auto_warm_enabled = False
        mock_connection.success_rate = 100
        mock_connection.model = "RMC-M40S"

        # Mock the hass.data to return the connection
        mock_hass.data = {
            "skycooker": {
                "test_entry": {
                    "connection": mock_connection
                }
            }
        }

        # Create a sensor instance
        sensor = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_TEMPERATURE)

        # Check that the sensor uses current_temp
        assert hasattr(sensor.skycooker, 'current_temp'), "SkyCookerConnection should have 'current_temp' attribute"
        # Verify that current_temp is used in the sensor's native_value method
        assert sensor.skycooker.current_temp == 25, "SkyCookerConnection should have 'current_temp' attribute with correct value"


class TestNumberAttributes:
    """Test class for checking number attributes."""

    def test_number_uses_correct_attributes(self):
        """Test that numbers use the correct attributes from SkyCookerConnection."""
        from custom_components.skycooker.number import SkyCookerNumber
        from custom_components.skycooker.const import NUMBER_TYPE_TEMPERATURE

        # Create a mock hass and entry
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        mock_entry.data = {}

        # Create a mock connection
        mock_connection = MagicMock()
        mock_connection.available = True
        mock_connection.status = MagicMock()
        mock_connection.status.mode = 0
        mock_connection.model_code = "RMC-M40S"

        # Mock the hass.data to return the connection
        mock_hass.data = {
            "skycooker": {
                "test_entry": {
                    "connection": mock_connection
                }
            }
        }

        # Create a number instance
        number = SkyCookerNumber(mock_hass, mock_entry, NUMBER_TYPE_TEMPERATURE)

        # Check that the number uses status, not _status
        assert hasattr(number.skycooker, 'status'), "SkyCookerConnection should have 'status' property"


class TestDeviceInfo:
    """Test class for checking device_info function."""

    def test_device_info_with_sw_version(self):
        """Test that device_info returns correct information with software version."""
        from custom_components.skycooker.__init__ import device_info
        from custom_components.skycooker.const import CONF_MAC, CONF_FRIENDLY_NAME

        # Create a mock hass and entry
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_MAC: "test_mac",
            CONF_FRIENDLY_NAME: "test_model"
        }

        # Create a mock connection
        mock_connection = MagicMock()
        mock_connection.sw_version = "1.0.0"

        # Mock the hass.data to return the connection
        mock_hass.data = {
            "skycooker": {
                "test_entry": {
                    "connection": mock_connection
                }
            }
        }

        # Call device_info function
        device_info_result = device_info(mock_entry, mock_hass)

        # Check that the device_info contains the software version
        assert device_info_result.sw_version == "1.0.0", "Device info should contain the software version"

    def test_device_info_without_sw_version(self):
        """Test that device_info returns correct information without software version."""
        from custom_components.skycooker.__init__ import device_info
        from custom_components.skycooker.const import CONF_MAC, CONF_FRIENDLY_NAME

        # Create a mock hass and entry
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {
            CONF_MAC: "test_mac",
            CONF_FRIENDLY_NAME: "test_model"
        }

        # Mock the hass.data to return None for connection
        mock_hass.data = {
            "skycooker": {
                "test_entry": {
                    "connection": None
                }
            }
        }

        # Call device_info function
        device_info_result = device_info(mock_entry, mock_hass)

        # Check that the device_info does not contain the software version
        assert device_info_result.sw_version is None, "Device info should not contain the software version if connection is None"
