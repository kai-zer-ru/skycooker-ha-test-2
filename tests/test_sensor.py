"""Tests for SkyCooker sensors."""
import pytest
from unittest.mock import MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_MAC, CONF_PASSWORD

from custom_components.skycooker.sensor import SkyCookerSensor
from custom_components.skycooker.const import *


@pytest.fixture
def hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.config = MagicMock()
    hass.config.language = "en"
    hass.data = {}
    hass.data[DOMAIN] = {}
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
    connection.current_temp = 25
    connection.remaining_time = 0
    connection.total_time = 0
    connection.auto_warm_enabled = False
    connection.success_rate = 100
    connection.sw_version = "1.0"
    return connection


def test_sensor_initialization(hass, entry, skycooker_connection):
    """Test sensor initialization."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_STATUS)
    assert sensor.unique_id == "test_entry_status"
    assert sensor.name == "SkyCooker Test Device status"
    assert sensor.icon == "mdi:information"


def test_sensor_available(hass, entry, skycooker_connection):
    """Test sensor availability."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_STATUS)
    assert sensor.available is True


def test_sensor_native_value_status(hass, entry, skycooker_connection):
    """Test sensor native value for status."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_STATUS)
    assert sensor.native_value == "Off"


def test_sensor_native_value_temperature(hass, entry, skycooker_connection):
    """Test sensor native value for temperature."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_TEMPERATURE)
    assert sensor.native_value == 25


def test_sensor_native_value_remaining_time(hass, entry, skycooker_connection):
    """Test sensor native value for remaining time."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_REMAINING_TIME)
    assert sensor.native_value == 0


def test_sensor_native_value_total_time(hass, entry, skycooker_connection):
    """Test sensor native value for total time."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_TOTAL_TIME)
    assert sensor.native_value == 0


def test_sensor_native_value_auto_warm_time(hass, entry, skycooker_connection):
    """Test sensor native value for auto warm time."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_AUTO_WARM_TIME)
    assert sensor.native_value == 0


def test_sensor_native_value_success_rate(hass, entry, skycooker_connection):
    """Test sensor native value for success rate."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_SUCCESS_RATE)
    assert sensor.native_value == 100


def test_sensor_native_value_delayed_launch_time(hass, entry, skycooker_connection):
    """Test sensor native value for delayed launch time."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_DELAYED_LAUNCH_TIME)
    assert sensor.native_value == 0


def test_sensor_native_value_sw_version(hass, entry, skycooker_connection):
    """Test sensor native value for software version."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_SW_VERSION)
    assert sensor.native_value == "1.0"


def test_sensor_device_class(hass, entry, skycooker_connection):
    """Test sensor device class."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_TEMPERATURE)
    assert sensor.device_class == "temperature"


def test_sensor_state_class(hass, entry, skycooker_connection):
    """Test sensor state class."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_TEMPERATURE)
    assert sensor.state_class == "measurement"


def test_sensor_native_unit_of_measurement(hass, entry, skycooker_connection):
    """Test sensor native unit of measurement."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_TEMPERATURE)
    assert sensor.native_unit_of_measurement == "°C"


def test_sensor_entity_category(hass, entry, skycooker_connection):
    """Test sensor entity category."""
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_SUCCESS_RATE)
    assert sensor.entity_category == "diagnostic"


def test_sensor_russian_language(hass, entry, skycooker_connection):
    """Test sensor with Russian language."""
    hass.config.language = "ru"
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_STATUS)
    assert sensor.name == "SkyCooker Test Device статус"
    assert sensor.native_value == "Выключена"


def test_sensor_unavailable(hass, entry, skycooker_connection):
    """Test sensor when skycooker is unavailable."""
    skycooker_connection.available = False
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CONNECTION: skycooker_connection,
        DATA_DEVICE_INFO: lambda: {"name": "Test Device"}
    }
    
    sensor = SkyCookerSensor(hass, entry, SENSOR_TYPE_STATUS)
    assert sensor.available is False
