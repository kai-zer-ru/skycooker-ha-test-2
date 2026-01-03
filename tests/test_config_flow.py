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
        mock_scanner_instance = AsyncMock()
        mock_scanner_instance.discovered_devices = []
        mock_scanner.return_value = mock_scanner_instance
        yield mock_scanner_instance


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
    # Добавляем устройство в список найденных устройств
    mock_bleak_scanner.discovered_devices = [mock_device]
    
    flow = SkyCookerConfigFlow()
    flow.hass = hass
    
    # Сначала вызываем async_step_scan для получения формы
    result = await flow.async_step_scan()
    
    # Проверяем, что форма была показана
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['step_id'] == 'scan'
    
    # Теперь имитируем выбор устройства пользователем
    user_input = {
        'mac': 'AA:BB:CC:DD:EE:FF (RMC-M40S)'
    }
    
    # Вызываем async_step_scan с выбором устройства
    result = await flow.async_step_scan(user_input)
    
    # Проверяем, что переход происходит на следующий шаг
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['step_id'] == 'parameters'
    
    # Теперь имитируем ввод параметров
    user_input = {
        CONF_PASSWORD: '1234567890ABCDEF',
        CONF_SCAN_INTERVAL: 60,
        CONF_USE_BACKLIGHT: False,
    }
    
    result = await flow.async_step_parameters(user_input)
    
    # Проверяем, что переход происходит на следующий шаг
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['step_id'] == 'instructions'
    
    # Имитируем нажатие "Продолжить"
    user_input = {'continue': True}
    result = await flow.async_step_instructions(user_input)
    
    # Проверяем, что переход происходит на следующий шаг
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['step_id'] == 'connect'
    
    # Имитируем нажатие "Подключиться"
    user_input = {'continue': True}
    result = await flow.async_step_connect(user_input)
    
    # Проверяем, что переход происходит на следующий шаг
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['step_id'] == 'connect'


async def test_user_step_invalid_password(hass: HomeAssistant, mock_bleak_scanner, mock_device):
    """Test user step with invalid password."""
    # Добавляем устройство в список найденных устройств
    mock_bleak_scanner.discovered_devices = [mock_device]
    
    flow = SkyCookerConfigFlow()
    flow.hass = hass
    
    # Сначала вызываем async_step_scan для получения формы
    result = await flow.async_step_scan()
    
    # Проверяем, что форма была показана
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['step_id'] == 'scan'
    
    # Теперь имитируем выбор устройства пользователем
    user_input = {
        'mac': 'AA:BB:CC:DD:EE:FF (RMC-M40S)'
    }
    
    # Вызываем async_step_scan с выбором устройства
    result = await flow.async_step_scan(user_input)
    
    # Проверяем, что переход происходит на следующий шаг
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['step_id'] == 'parameters'
    
    # Теперь имитируем ввод параметров с неверным паролем
    user_input = {
        CONF_PASSWORD: 'invalid',
        CONF_SCAN_INTERVAL: 60,
        CONF_USE_BACKLIGHT: False,
    }
    
    result = await flow.async_step_parameters(user_input)
    
    # Проверяем, что возвращается форма с ошибкой
    assert result['type'] == data_entry_flow.FlowResultType.FORM
    assert result['step_id'] == 'parameters'
    assert 'password' in result['errors']
    assert 'password' in result['errors']


async def test_user_step_unsupported_device(hass: HomeAssistant, mock_bleak_scanner):
    """Test user step with unsupported device."""
    mock_device = AsyncMock()
    mock_device.name = 'Unsupported-Device'
    mock_device.address = 'AA:BB:CC:DD:EE:FF'
    # Добавляем устройство в список найденных устройств
    mock_bleak_scanner.discovered_devices = [mock_device]

    flow = SkyCookerConfigFlow()
    flow.hass = hass

    # Сначала вызываем async_step_scan для получения формы
    result = await flow.async_step_scan()

    # Проверяем, что возвращается ошибка о неподдерживаемом устройстве
    assert result['type'] == data_entry_flow.FlowResultType.ABORT
    assert result['reason'] == 'cooker_not_found'


async def test_user_step_device_not_found(hass: HomeAssistant, mock_bleak_scanner):
    """Test user step when device not found."""
    # Пустой список устройств
    mock_bleak_scanner.discovered_devices = []

    flow = SkyCookerConfigFlow()
    flow.hass = hass

    # Сначала вызываем async_step_scan для получения формы
    result = await flow.async_step_scan()

    # Проверяем, что возвращается ошибка о ненайденном устройстве
    assert result['type'] == data_entry_flow.FlowResultType.ABORT
    assert result['reason'] == 'cooker_not_found'