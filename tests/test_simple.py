"""Простые тесты для проверки загрузки интеграции SkyCooker."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.skycooker.const import DOMAIN, CONF_MAC, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USE_BACKLIGHT


def test_imports():
    """Тест импортов."""
    from custom_components.skycooker import async_setup_entry, async_unload_entry
    assert callable(async_setup_entry)
    assert callable(async_unload_entry)


@pytest.mark.asyncio
async def test_setup_entry_signature():
    """Тест сигнатуры функции setup_entry."""
    from custom_components.skycooker import async_setup_entry
    
    # Проверяем, что функция принимает правильные аргументы
    import inspect
    sig = inspect.signature(async_setup_entry)
    params = list(sig.parameters.keys())
    assert 'hass' in params
    assert 'config_entry' in params


@pytest.mark.asyncio
async def test_unload_entry_signature():
    """Тест сигнатуры функции unload_entry."""
    from custom_components.skycooker import async_unload_entry
    
    # Проверяем, что функция принимает правильные аргументы
    import inspect
    sig = inspect.signature(async_unload_entry)
    params = list(sig.parameters.keys())
    assert 'hass' in params
    assert 'entry' in params


def test_constants():
    """Тест констант."""
    from custom_components.skycooker.const import (
        DOMAIN, CONF_MAC, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USE_BACKLIGHT,
        SUPPORTED_DOMAINS, COOKER_PROGRAMS, STATUS_OFF, STATUS_ON
    )
    
    assert DOMAIN == "skycooker"
    assert CONF_MAC == "mac"
    assert CONF_PASSWORD == "password"
    assert CONF_SCAN_INTERVAL == "scan_interval"
    assert CONF_USE_BACKLIGHT == "use_backlight"
    assert isinstance(SUPPORTED_DOMAINS, list)
    assert len(SUPPORTED_DOMAINS) > 0
    assert isinstance(COOKER_PROGRAMS, dict)
    assert len(COOKER_PROGRAMS) > 0
    assert STATUS_OFF == '00'
    assert STATUS_ON == '02'