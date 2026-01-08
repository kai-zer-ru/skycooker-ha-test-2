"""Tests for SkyCooker select entities."""
import pytest
from unittest.mock import MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_MAC, CONF_PASSWORD

from custom_components.skycooker.select import SkyCookerSelect
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
    connection.current_mode = 0
    connection.model_code = MODEL_3
    connection.target_state = None
    connection.target_boil_time = None
    return connection


def test_select_initialization(hass, entry, skycooker_connection):
    """Test select entity initialization."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    assert select.unique_id == "test_entry_mode"
    assert select.name == "SkyCooker Test Device режим"
    assert select.icon == "mdi:chef-hat"


def test_select_available(hass, entry, skycooker_connection):
    """Test select entity availability."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    assert select.available is True


def test_select_current_option(hass, entry, skycooker_connection):
    """Test select entity current option."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    assert select.current_option == "Multi-chef"


def test_select_options(hass, entry, skycooker_connection):
    """Test select entity options."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    assert len(select.options) > 0
    assert "Multi-chef" in select.options


@pytest.mark.asyncio
async def test_select_option(hass, entry, skycooker_connection):
    """Test select entity option selection."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    skycooker_connection.set_target_mode = MagicMock()
    skycooker_connection.set_target_mode = AsyncMock()
    await select.async_select_option("Multi-chef")
    assert skycooker_connection.set_target_mode.called


def test_select_unavailable(hass, entry, skycooker_connection):
    """Test select entity when skycooker is unavailable."""
    skycooker_connection.available = False
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    assert select.available is False


def test_select_russian_language(hass, entry, skycooker_connection):
    """Test select entity with Russian language."""
    hass.config.language = "ru"
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    assert select.current_option == "Мультиповар"
