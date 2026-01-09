"""Tests for SkyCooker switch entities."""
import pytest
from unittest.mock import MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_MAC, CONF_PASSWORD

from custom_components.skycooker.switch import SkyCookerSwitch
from custom_components.skycooker.const import *

from unittest.mock import AsyncMock


@pytest.fixture
def hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.config = MagicMock()
    hass.config.language = "en"
    hass.data = {}
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DATA_DEVICE_INFO] = lambda: {"name": "Test Device"}
    hass.loop = MagicMock()
    return hass


@pytest.fixture
def entry():
    """Create a mock ConfigEntry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.data = {
        CONF_FRIENDLY_NAME: "Test Device",
        CONF_MAC: "00:11:22:33:44:55",
        CONF_PASSWORD: "test_password",
        CONF_PERSISTENT_CONNECTION: True
    }
    return entry


@pytest.fixture
def skycooker_connection():
    """Create a mock SkyCookerConnection."""
    connection = MagicMock()
    connection.available = True
    connection.status_code = STATUS_OFF
    connection.current_mode = 0
    connection.model_code = MODEL_3
    connection.target_boil_hours = None
    connection.target_boil_minutes = None
    return connection


@pytest.mark.asyncio
async def test_switch_auto_warm_enable(hass, entry, skycooker_connection):
    """Test auto warm switch enable."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    switch = SkyCookerSwitch(hass, entry, SWITCH_TYPE_AUTO_WARM)
    
    # Mock the enable_auto_warm method to set the flag
    async def mock_enable_auto_warm():
        skycooker_connection._auto_warm_enabled = True
    
    skycooker_connection.enable_auto_warm = mock_enable_auto_warm
    skycooker_connection._auto_warm_enabled = False
    
    await switch.async_turn_on()
    
    # Verify enable_auto_warm was called
    assert skycooker_connection._auto_warm_enabled == True


@pytest.mark.asyncio
async def test_switch_auto_warm_disable(hass, entry, skycooker_connection):
    """Test auto warm switch disable."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    switch = SkyCookerSwitch(hass, entry, SWITCH_TYPE_AUTO_WARM)
    
    # Mock the disable_auto_warm method to clear the flag
    async def mock_disable_auto_warm():
        skycooker_connection._auto_warm_enabled = False
    
    skycooker_connection.disable_auto_warm = mock_disable_auto_warm
    skycooker_connection._auto_warm_enabled = True
    
    await switch.async_turn_off()
    
    # Verify disable_auto_warm was called
    assert skycooker_connection._auto_warm_enabled == False
