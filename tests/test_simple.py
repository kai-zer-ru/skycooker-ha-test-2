"""Простой тест интеграции SkyCooker."""

import pytest
from custom_components.skycooker.const import (
    DOMAIN, SUPPORTED_DOMAINS, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL,
    CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION,
    CONF_USE_BACKLIGHT, DEVICE_TYPE_COOKER, SUPPORTED_DEVICES, COOKER_PROGRAMS,
    STATUS_OFF, STATUS_ON, COOKER_STATUS_PROGRAM, COOKER_STATUS_KEEP_WARM,
    COOKER_STATUS_DELAYED_START, MODE_MANUAL, MODE_AUTO, MIN_TEMP, MAX_TEMP,
    MIN_HOURS, MAX_HOURS, MIN_MINUTES, MAX_MINUTES
)


def test_all_constants():
    """Тест всех констант."""
    # Проверяем основные константы
    assert DOMAIN == "skycooker"
    assert SUPPORTED_DOMAINS == ['sensor', 'switch', 'number', 'select']
    assert CONF_SCAN_INTERVAL == "scan_interval"
    assert DEFAULT_SCAN_INTERVAL == 30
    assert CONF_PERSISTENT_CONNECTION == "persistent_connection"
    assert DEFAULT_PERSISTENT_CONNECTION is True
    assert CONF_USE_BACKLIGHT == "use_backlight"
    assert DEVICE_TYPE_COOKER == 5
    assert 'RMC-M40S' in SUPPORTED_DEVICES
    assert SUPPORTED_DEVICES['RMC-M40S'] == DEVICE_TYPE_COOKER
    assert 'rice' in COOKER_PROGRAMS
    assert 'slow_cooking' in COOKER_PROGRAMS
    assert 'baking' in COOKER_PROGRAMS
    assert STATUS_OFF == '00'
    assert STATUS_ON == '02'
    assert COOKER_STATUS_PROGRAM == '01'
    assert COOKER_STATUS_KEEP_WARM == '04'
    assert COOKER_STATUS_DELAYED_START == '05'
    assert MODE_MANUAL == '00'
    assert MODE_AUTO == '01'
    assert MIN_TEMP == 35
    assert MAX_TEMP == 200
    assert MIN_HOURS == 0
    assert MAX_HOURS == 23
    assert MIN_MINUTES == 0
    assert MAX_MINUTES == 59


def test_programs_structure():
    """Тест структуры программ."""
    # Проверяем, что все программы имеют правильную структуру
    for program_name, program_data in COOKER_PROGRAMS.items():
        assert isinstance(program_name, str)
        assert isinstance(program_data, list)
        assert len(program_data) == 8  # Все программы должны иметь 8 элементов
        # Проверяем, что все элементы - строки
        for item in program_data:
            assert isinstance(item, str)


def test_imports():
    """Тест импортов."""
    # Проверяем, что все необходимые модули импортируются
    from custom_components.skycooker import async_setup_entry, async_unload_entry
    from custom_components.skycooker.const import DOMAIN, SUPPORTED_DOMAINS
    
    # Проверяем, что функции существуют
    assert callable(async_setup_entry)
    assert callable(async_unload_entry)