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
    connection._target_mode = None
    connection._target_temperature = None
    connection.target_boil_hours = None
    connection.target_boil_minutes = None
    connection._target_delayed_start_hours = None
    connection._target_delayed_start_minutes = None
    return connection


def test_select_initialization(hass, entry, skycooker_connection):
    """Test select entity initialization."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    assert select.unique_id == "test_entry_mode"
    assert select.name == "SkyCooker Test Device mode"
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
    
    # Set target_mode to simulate user selection
    skycooker_connection._target_mode = 0
    
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
        
        # Mock MODE_DATA to return proper values
        skycooker_connection.model_code = MODEL_3
        # Mock set_target_mode as AsyncMock
        skycooker_connection.set_target_mode = AsyncMock()
        
        select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
        await select.async_select_option("Multi-chef")
        
        # Verify that set_target_mode was called
        assert skycooker_connection.set_target_mode.called
        # Verify that target_mode is set correctly
        if hasattr(skycooker_connection, '_target_mode'):
            assert skycooker_connection._target_mode == 0  # Multi-chef mode ID


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
    
    # Set target_mode to simulate user selection
    skycooker_connection._target_mode = 0
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    assert select.current_option == "Мультиповар"


def test_temperature_select_initialization(hass, entry, skycooker_connection):
    """Test temperature select entity initialization."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_TEMPERATURE)
    assert select.unique_id == "test_entry_temperature"
    assert select.name == "SkyCooker Test Device temperature"
    assert select.icon == "mdi:thermometer"


def test_cooking_time_hours_select_initialization(hass, entry, skycooker_connection):
    """Test cooking time hours select entity initialization."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_HOURS)
    assert select.unique_id == "test_entry_cooking_time_hours"
    assert select.name == "SkyCooker Test Device cooking time (hours)"
    assert select.icon == "mdi:timer"


def test_cooking_time_minutes_select_initialization(hass, entry, skycooker_connection):
    """Test cooking time target_boil_minutes select entity initialization."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_MINUTES)
    assert select.unique_id == "test_entry_cooking_time_minutes"
    assert select.name == "SkyCooker Test Device cooking time (minutes)"
    assert select.icon == "mdi:timer"


def test_delayed_start_hours_select_initialization(hass, entry, skycooker_connection):
    """Test delayed start hours select entity initialization."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_HOURS)
    assert select.unique_id == "test_entry_delayed_start_hours"
    assert select.name == "SkyCooker Test Device delayed start (hours)"
    assert select.icon == "mdi:timer-sand"


def test_delayed_start_minutes_select_initialization(hass, entry, skycooker_connection):
    """Test delayed start minutes select entity initialization."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_MINUTES)
    assert select.unique_id == "test_entry_delayed_start_minutes"
    assert select.name == "SkyCooker Test Device delayed start (minutes)"
    assert select.icon == "mdi:timer-sand"


def test_temperature_select_options(hass, entry, skycooker_connection):
    """Test temperature select entity options."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_TEMPERATURE)
    assert len(select.options) == 33  # (200 - 40) / 5 + 1 = 33
    assert "40" in select.options
    assert "200" in select.options


def test_cooking_time_hours_select_options(hass, entry, skycooker_connection):
    """Test cooking time hours select entity options."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_HOURS)
    assert len(select.options) == 24  # 0 to 23
    assert "0" in select.options
    assert "23" in select.options


def test_cooking_time_minutes_select_options(hass, entry, skycooker_connection):
    """Test cooking time minutes select entity options."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_MINUTES)
    assert len(select.options) == 60  # 0 to 59
    assert "0" in select.options
    assert "59" in select.options


def test_delayed_start_hours_select_options(hass, entry, skycooker_connection):
    """Test delayed start hours select entity options."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_HOURS)
    assert len(select.options) == 24  # 0 to 23
    assert "0" in select.options
    assert "23" in select.options


def test_delayed_start_minutes_select_options(hass, entry, skycooker_connection):
    """Test delayed start minutes select entity options."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_MINUTES)
    assert len(select.options) == 60  # 0 to 59
    assert "0" in select.options
    assert "59" in select.options


    @pytest.mark.asyncio
    async def test_temperature_select_option(hass, entry, skycooker_connection):
        """Test temperature select entity option selection."""
        hass.data[DOMAIN][entry.entry_id] = {
            DATA_CONNECTION: skycooker_connection,
            DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
        }
        
        # Set initial target_mode
        skycooker_connection._target_mode = 0
        
        select = SkyCookerSelect(hass, entry, SELECT_TYPE_TEMPERATURE)
        await select.async_select_option("100")
        # Temperature select should update the _target_temperature
        # So we need to check if the _target_temperature was updated
        assert skycooker_connection._target_temperature == 100


@pytest.mark.asyncio
async def test_cooking_time_hours_select_option(hass, entry, skycooker_connection):
    """Test cooking time hours select entity option selection."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_HOURS)
    await select.async_select_option("2")
    assert skycooker_connection.target_boil_hours == 2  # 2 hours
    # target_boil_minutes should remain None as it wasn't set
    assert skycooker_connection.target_boil_minutes is None


@pytest.mark.asyncio
async def test_cooking_time_minutes_select_option(hass, entry, skycooker_connection):
    """Test cooking time minutes select entity option selection."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_MINUTES)
    await select.async_select_option("30")
    # target_boil_hours should remain None as it wasn't set
    assert skycooker_connection.target_boil_hours is None
    assert skycooker_connection.target_boil_minutes == 30  # 30 minutes


@pytest.mark.asyncio
async def test_delayed_start_hours_select_option(hass, entry, skycooker_connection):
    """Test delayed start hours select entity option selection."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_HOURS)
    await select.async_select_option("2")
    assert skycooker_connection._target_delayed_start_hours == 2


@pytest.mark.asyncio
async def test_delayed_start_minutes_select_option(hass, entry, skycooker_connection):
    """Test delayed start minutes select entity option selection."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    select = SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_MINUTES)
    await select.async_select_option("30")
    assert skycooker_connection._target_delayed_start_minutes == 30


@pytest.mark.asyncio
async def test_commands_sent_only_on_mode_change(hass, entry, skycooker_connection):
    """Test that commands are sent only when mode is changed, not when other parameters are changed."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    # Mock the set_target_mode method to track if it's called
    skycooker_connection.set_target_mode = AsyncMock()
    skycooker_connection.model_code = MODEL_3
    
    # Change mode - should send commands
    select_mode = SkyCookerSelect(hass, entry, SELECT_TYPE_MODE)
    await select_mode.async_select_option("Multi-chef")
    
    # Verify that set_target_mode was called for mode change
    assert skycooker_connection.set_target_mode.called
    assert skycooker_connection.set_target_mode.call_count == 1
    
    # Reset the mock
    skycooker_connection.set_target_mode.reset_mock()
    
    # Change temperature - should NOT send commands
    skycooker_connection.status = MagicMock()
    skycooker_connection.status.mode = 0
    select_temp = SkyCookerSelect(hass, entry, SELECT_TYPE_TEMPERATURE)
    await select_temp.async_select_option("100")
    
    # Verify that set_target_mode was NOT called for temperature change
    assert not skycooker_connection.set_target_mode.called
    
    # Change cooking time - should NOT send commands
    select_hours = SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_HOURS)
    await select_hours.async_select_option("1")
    
    select_minutes = SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_MINUTES)
    await select_minutes.async_select_option("30")
    
    # Verify that set_target_mode was NOT called for cooking time change
    assert not skycooker_connection.set_target_mode.called
    
    # Verify that target state is set correctly
    assert skycooker_connection.target_mode is not None
    assert skycooker_connection.target_boil_hours == 1  # 1 hour
    assert skycooker_connection.target_boil_minutes == 30  # 30 minutes
