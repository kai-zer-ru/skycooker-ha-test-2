#!/usr/bin/env python3
# coding: utf-8

"""Тест для проверки функции async_step_user."""

import unittest
from unittest.mock import Mock, patch, AsyncMock
from custom_components.skycooker.config_flow import SkyCookerConfigFlow
from custom_components.skycooker.const import SUPPORTED_DEVICES, DOMAIN


class TestConfigFlowUserStep(unittest.TestCase):
    """Тесты для проверки функции async_step_user."""

    def setUp(self):
        """Настройка теста."""
        self.hass = Mock()
        self.flow = SkyCookerConfigFlow()

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_user_step_calls_scan(self, mock_bluetooth):
        """Тест что async_step_user вызывает async_step_scan."""
        # Создаем mock устройства
        mock_device = Mock()
        mock_device.address = "DA:D8:9F:9E:0B:4C"
        mock_device.name = "RMC-M40S"
        
        # Создаем mock сканер
        mock_scanner = Mock()
        mock_scanner.discovered_devices = [mock_device]
        mock_bluetooth.async_get_scanner.return_value = mock_scanner
        
        # Устанавливаем hass в flow
        self.flow.hass = self.hass
        
        # Мокаем async_step_scan для проверки вызова
        with patch.object(self.flow, 'async_step_scan', return_value=AsyncMock()) as mock_scan:
            # Вызываем async_step_user
            result = await self.flow.async_step_user()
            
            # Проверяем, что async_step_scan был вызван
            mock_scan.assert_called_once_with(None)
            _LOGGER.debug("✅ async_step_user корректно вызывает async_step_scan")

    async def test_user_step_with_user_input(self):
        """Тест что async_step_user корректно обрабатывает user_input."""
        # Мокаем async_step_scan для проверки вызова с user_input
        with patch.object(self.flow, 'async_step_scan', return_value=AsyncMock()) as mock_scan:
            user_input = {'test': 'data'}
            # Вызываем async_step_user с user_input
            result = await self.flow.async_step_user(user_input)
            
            # Проверяем, что async_step_scan был вызван с user_input
            mock_scan.assert_called_once_with(user_input)
            _LOGGER.debug("✅ async_step_user корректно передает user_input в async_step_scan")


if __name__ == '__main__':
    unittest.main()