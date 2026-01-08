#!/usr/local/bin/python3
"""Tests for SkyCooker config flow."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.const import CONF_MAC, CONF_FRIENDLY_NAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from custom_components.skycooker.config_flow import SkyCookerConfigFlow
from custom_components.skycooker.const import DOMAIN, CONF_PERSISTENT_CONNECTION, DEFAULT_SCAN_INTERVAL, DEFAULT_PERSISTENT_CONNECTION


class TestSkyCookerConfigFlow:
    """Test class for SkyCookerConfigFlow."""

    def test_config_flow_initialization(self):
        """Test that the config flow initializes correctly."""
        mock_hass = MagicMock()
        flow = SkyCookerConfigFlow()

        assert flow.VERSION == 1
        assert flow.entry is None
        assert flow.config == {}

    def test_config_flow_initialization_with_entry(self):
        """Test that the config flow initializes correctly with an entry."""
        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_entry.data = {"test_key": "test_value"}
        flow = SkyCookerConfigFlow(entry=mock_entry)

        assert flow.VERSION == 1
        assert flow.entry == mock_entry
        assert flow.config == {"test_key": "test_value"}

    @pytest.mark.asyncio
    async def test_init_mac(self):
        """Test that the init_mac method correctly formats the MAC address."""
        mock_hass = MagicMock()
        flow = SkyCookerConfigFlow()
        flow._async_current_ids = MagicMock(return_value=[])
        flow.async_set_unique_id = AsyncMock()

        result = await flow.init_mac("AA:BB:CC:DD:EE:FF")

        assert result == True
        assert flow.config[CONF_MAC] == "AA:BB:CC:DD:EE:FF"
        assert flow.config[CONF_PASSWORD] == list(bytes.fromhex("0000000000000000"))

    @pytest.mark.asyncio
    async def test_init_mac_already_configured(self):
        """Test that the init_mac method returns False if the device is already configured."""
        mock_hass = MagicMock()
        flow = SkyCookerConfigFlow()
        flow._async_current_ids = MagicMock(return_value=[f"{DOMAIN}-AA:BB:CC:DD:EE:FF"])

        result = await flow.init_mac("AA:BB:CC:DD:EE:FF")

        assert result == False

    @pytest.mark.asyncio
    @patch("custom_components.skycooker.config_flow.SkyCooker")
    async def test_async_step_scan(self, mock_skycooker):
        """Test that the async_step_scan method correctly handles the scan step."""
        mock_hass = MagicMock()
        flow = SkyCookerConfigFlow()
        flow.hass = mock_hass

        mock_device1 = MagicMock()
        mock_device1.address = "AA:BB:CC:DD:EE:FF"
        mock_device1.name = "RMC-TestDevice"

        mock_device2 = MagicMock()
        mock_device2.address = "11:22:33:44:55:66"
        mock_device2.name = "RFS-AnotherDevice"

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices = [mock_device1, mock_device2]

        mock_bluetooth = MagicMock()
        mock_bluetooth.async_get_scanner = MagicMock(return_value=mock_scanner)

        with patch("custom_components.skycooker.config_flow.bluetooth", mock_bluetooth):
            with patch("custom_components.skycooker.config_flow.vol.Schema"):
                result = await flow.async_step_scan()

                assert result["step_id"] == "scan"

    @pytest.mark.asyncio
    async def test_async_step_connect(self):
        """Test that the async_step_connect method correctly handles the connect step."""
        mock_hass = MagicMock()
        flow = SkyCookerConfigFlow()
        flow.hass = mock_hass
        flow.config = {
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
            CONF_FRIENDLY_NAME: "Test Device"
        }

        mock_connection = MagicMock()
        mock_connection.last_connect_ok = True
        mock_connection.last_auth_ok = True
        mock_connection.update = AsyncMock()
        mock_connection.stop = MagicMock()

        with patch("custom_components.skycooker.config_flow.SkyCookerConnection", return_value=mock_connection):
            result = await flow.async_step_connect(user_input={})

            assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_async_step_init(self):
        """Test that the async_step_init method correctly handles the init step."""
        mock_hass = MagicMock()
        flow = SkyCookerConfigFlow()
        flow.hass = mock_hass
        flow.config = {
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
            CONF_FRIENDLY_NAME: "Test Device",
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_PERSISTENT_CONNECTION: DEFAULT_PERSISTENT_CONNECTION
        }

        user_input = {
            CONF_SCAN_INTERVAL: 10,
            CONF_PERSISTENT_CONNECTION: True
        }

        with patch("custom_components.skycooker.config_flow.vol.Schema"):
            result = await flow.async_step_init(user_input)

            assert result["type"] == "create_entry"
            assert flow.config[CONF_SCAN_INTERVAL] == 10
            assert flow.config[CONF_PERSISTENT_CONNECTION] == True