#!/usr/local/bin/python3
# coding: utf-8

import pytest
from unittest.mock import patch, AsyncMock
from homeassistant import data_entry_flow
from homeassistant.const import CONF_MAC, CONF_PASSWORD, CONF_SCAN_INTERVAL
from custom_components.skycooker.const import CONF_USE_BACKLIGHT
from homeassistant.core import HomeAssistant

from custom_components.skycooker.const import SUPPORTED_DEVICES
from custom_components.skycooker.config_flow import SkyCookerConfigFlow


@pytest.fixture
def mock_bleak_scanner():
    """Mock BleakScanner."""
    with patch('custom_components.skycooker.config_flow.bluetooth.async_get_scanner') as mock_scanner:
        yield mock_scanner


@pytest.fixture
def mock_device():
    """Mock device."""
    device = AsyncMock()
    device.name = 'RMC-M40S'
    device.address = 'AA:BB:CC:DD:EE:FF'
    return device


@pytest.fixture
def hass():
    """Mock HomeAssistant."""
    return AsyncMock()


async def test_user_step_success(hass: HomeAssistant, mock_bleak_scanner, mock_device):
    """Test successful user step."""
    mock_bleak_scanner.find_device_by_address.return_value = mock_device
    
    flow = SkyCookerConfigFlow()
    result = await flow.async_step_user({
        CONF_MAC: 'AA:BB:CC:DD:EE:FF',
        CONF_PASSWORD: '1234567890ABCDEF',
        CONF_SCAN_INTERVAL: 60,
        CONF_USE_BACKLIGHT: False,
    })
    
    assert result['type'] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result['title'] == 'RMC-M40S'
    assert result['data'][CONF_MAC] == 'AA:BB:CC:DD:EE:FF'
    assert result['data'][CONF_PASSWORD] == '1234567890ABCDEF'


async def test_user_step_invalid_password(hass: HomeAssistant, mock_bleak_scanner, mock_device):
    """Test user step with invalid password."""
    mock_bleak_scanner.find_device_by_address.return_value = mock_device
    
    flow = SkyCookerConfigFlow()
    result = await flow.async_step_user({
        CONF_MAC: 'AA:BB:CC:DD:EE:FF',
        CONF_PASSWORD: 'invalid',
        CONF_SCAN_INTERVAL: 60,
        CONF_USE_BACKLIGHT: False,
    })
    
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['errors']['base'] == 'wrong_password'


async def test_user_step_unsupported_device(hass: HomeAssistant, mock_bleak_scanner):
    """Test user step with unsupported device."""
    mock_device = AsyncMock()
    mock_device.name = 'Unsupported-Device'
    mock_device.address = 'AA:BB:CC:DD:EE:FF'
    mock_bleak_scanner.find_device_by_address.return_value = mock_device
    
    flow = SkyCookerConfigFlow()
    result = await flow.async_step_user({
        CONF_MAC: 'AA:BB:CC:DD:EE:FF',
        CONF_PASSWORD: '1234567890ABCDEF',
        CONF_SCAN_INTERVAL: 60,
        CONF_USE_BACKLIGHT: False,
    })
    
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['errors']['base'] == 'unsupported_device'


async def test_user_step_device_not_found(hass: HomeAssistant, mock_bleak_scanner):
    """Test user step when device not found."""
    mock_bleak_scanner.find_device_by_address.return_value = None
    
    flow = SkyCookerConfigFlow()
    result = await flow.async_step_user({
        CONF_MAC: 'AA:BB:CC:DD:EE:FF',
        CONF_PASSWORD: '1234567890ABCDEF',
        CONF_SCAN_INTERVAL: 60,
        CONF_USE_BACKLIGHT: False,
    })
    
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['errors']['base'] == 'device_not_found'