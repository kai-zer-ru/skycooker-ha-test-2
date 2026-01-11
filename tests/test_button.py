#!/usr/local/bin/python3
"""Tests for SkyCooker button entities."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.skycooker.button import SkyCookerButton
from custom_components.skycooker.const import BUTTON_TYPE_START, BUTTON_TYPE_STOP, BUTTON_TYPE_START_DELAYED, DATA_DEVICE_INFO


class TestSkyCookerButton:
    """Test class for SkyCookerButton."""

    def test_button_initialization(self):
        """Test that the button entity initializes correctly."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        mock_entry.data = {"friendly_name": "Test Device"}

        button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)

        assert button.hass == mock_hass
        assert button.entry == mock_entry
        assert button.button_type == BUTTON_TYPE_START

    def test_button_unique_id(self):
        """Test that the button entity returns the correct unique ID."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        mock_entry.data = {"friendly_name": "Test Device"}

        button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
    
        assert button.unique_id == "button.skycooker_start_Test_Device_test_entry"

    def test_button_name(self):
        """Test that the button entity returns the correct name."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        mock_entry.data = {"friendly_name": "Test Device"}

        button_start = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
        button_stop = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_STOP)
        button_delayed = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START_DELAYED)
    
        assert button_start.name == "SkyCooker Test Device start"
        assert button_stop.name == "SkyCooker Test Device stop"
        assert button_delayed.name == "SkyCooker Test Device start delayed"

    def test_button_icon(self):
        """Test that the button entity returns the correct icon."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        button_start = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
        button_stop = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_STOP)
        button_delayed = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START_DELAYED)

        assert button_start.icon == "mdi:play"
        assert button_stop.icon == "mdi:stop"
        assert button_delayed.icon == "mdi:timer-play"

    def test_button_available(self):
        """Test that the button entity returns the correct availability."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        mock_connection = MagicMock()
        mock_connection.available = True

        mock_hass.data = {
            "skycooker": {
                "test_entry": {
                    "connection": mock_connection
                }
            }
        }

        button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)

        assert button.available == True

    @pytest.mark.asyncio
    async def test_button_press_start(self):
        """Test that the button entity correctly handles the start button press."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        mock_connection = MagicMock()
        mock_connection.available = True
        mock_connection.start = AsyncMock()

        mock_hass.data = {
            "skycooker": {
                "test_entry": {
                    "connection": mock_connection
                }
            }
        }

        button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)

        await button.async_press()

        mock_connection.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_button_press_stop(self):
        """Test that the button entity correctly handles the stop button press."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"
        
        mock_connection = MagicMock()
        mock_connection.available = True
        mock_connection.stop_cooking = AsyncMock()
        
        mock_hass.data = {
            "skycooker": {
                "test_entry": {
                    "connection": mock_connection
                }
            }
        }
        
        button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_STOP)
        
        await button.async_press()
        
        mock_connection.stop_cooking.assert_called_once()

    @pytest.mark.asyncio
    async def test_button_press_delayed(self):
        """Test that the button entity correctly handles the delayed start button press."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry"

        mock_connection = MagicMock()
        mock_connection.available = True
        mock_connection.start_delayed = AsyncMock()

        mock_hass.data = {
            "skycooker": {
                "test_entry": {
                    "connection": mock_connection
                }
            }
        }

        button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START_DELAYED)

        await button.async_press()

        mock_connection.start_delayed.assert_called_once()

    def test_button_device_info(self):
            """Test that the button entity returns the correct device info."""
            mock_hass = MagicMock()
            mock_entry = MagicMock()
            mock_entry.entry_id = "test_entry"
    
            mock_device_info = {"name": "Test Device"}
    
            mock_hass.data = {
                "skycooker": {
                    DATA_DEVICE_INFO: lambda: mock_device_info
                }
            }
    
            button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
    
            assert button.device_info == mock_device_info