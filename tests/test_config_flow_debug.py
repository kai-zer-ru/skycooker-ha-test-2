#!/usr/bin/env python3
# coding: utf-8

"""Тест для отладки логики сканирования устройств в config_flow."""

import unittest
from unittest.mock import Mock, patch, AsyncMock
from custom_components.skycooker.config_flow import SkyCookerConfigFlow
from custom_components.skycooker.const import SUPPORTED_DEVICES, DOMAIN


class TestConfigFlowDebug(unittest.TestCase):
    """Тесты для отладки логики сканирования."""

    def setUp(self):
        """Настройка теста."""
        self.hass = Mock()
        self.flow = SkyCookerConfigFlow()

    @patch('custom_components.skycooker.config_flow.bluetooth')
    def test_device_filtering(self, mock_bluetooth):
        """Тест фильтрации устройств по поддерживаемым моделям."""
        # Создаем mock устройства
        mock_device = Mock()
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        mock_device.name = "RMC-M40S"
        
        # Создаем mock сканер
        mock_scanner = Mock()
        mock_scanner.discovered_devices = [mock_device]
        mock_bluetooth.async_get_scanner.return_value = mock_scanner
        
        # Проверяем, что устройство проходит фильтрацию
        self.assertIn(mock_device.name, SUPPORTED_DEVICES)
        self.assertEqual(mock_device.name, "RMC-M40S")

    @patch('custom_components.skycooker.config_flow.bluetooth')
    def test_unsupported_device_filtering(self, mock_bluetooth):
        """Тест фильтрации неподдерживаемых устройств."""
        # Создаем mock устройства с неподдерживаемым именем
        mock_device = Mock()
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        mock_device.name = "Unknown_Device"
        
        # Создаем mock сканер
        mock_scanner = Mock()
        mock_scanner.discovered_devices = [mock_device]
        mock_bluetooth.async_get_scanner.return_value = mock_scanner
        
        # Проверяем, что устройство не проходит фильтрацию
        self.assertNotIn(mock_device.name, SUPPORTED_DEVICES)

    def test_supported_devices_list(self):
        """Тест списка поддерживаемых устройств."""
        expected_devices = [
            'RMC-M40S',
            'RMC-M800S', 
            'RMC-M223S',
            'RMC-M92S',
            'RMC-M92S-E'
        ]
        
        self.assertEqual(list(SUPPORTED_DEVICES.keys()), expected_devices)
        self.assertEqual(len(SUPPORTED_DEVICES), 5)


if __name__ == '__main__':
    unittest.main()