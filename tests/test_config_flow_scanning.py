#!/usr/bin/env python3
# coding: utf-8

"""Комплексный тест для проверки логики сканирования устройств."""

import unittest
from unittest.mock import Mock, patch, AsyncMock
from custom_components.skycooker.config_flow import SkyCookerConfigFlow
from custom_components.skycooker.const import SUPPORTED_DEVICES, DOMAIN


class TestConfigFlowScanning(unittest.TestCase):
    """Комплексные тесты для логики сканирования."""

    def setUp(self):
        """Настройка теста."""
        self.hass = Mock()
        self.flow = SkyCookerConfigFlow()

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_scan_with_supported_device(self, mock_bluetooth):
        """Тест сканирования с поддерживаемым устройством."""
        # Создаем mock устройства
        mock_device = Mock()
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        mock_device.name = "RMC-M40S"
        
        # Создаем mock сканер
        mock_scanner = Mock()
        mock_scanner.discovered_devices = [mock_device]
        mock_bluetooth.async_get_scanner.return_value = mock_scanner
        
        # Устанавливаем hass в flow
        self.flow.hass = self.hass
        
        # Вызываем async_step_scan без user_input (начало сканирования)
        result = await self.flow.async_step_scan()
        
        # Проверяем, что форма была показана с правильными данными
        self.assertEqual(result['type'], 'form')
        self.assertEqual(result['step_id'], 'scan')
        self.assertIn('data_schema', result)
        
        # Проверяем, что в схеме есть наше устройство
        schema = result['data_schema']
        mac_list = list(schema.schema['mac'].container.keys())
        self.assertIn("AA:BB:CC:DD:EE:FF (RMC-M40S)", mac_list)

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_scan_with_unsupported_device(self, mock_bluetooth):
        """Тест сканирования с неподдерживаемым устройством."""
        # Создаем mock устройства
        mock_device = Mock()
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        mock_device.name = "Unknown_Device"
        
        # Создаем mock сканер
        mock_scanner = Mock()
        mock_scanner.discovered_devices = [mock_device]
        mock_bluetooth.async_get_scanner.return_value = mock_scanner
        
        # Устанавливаем hass в flow
        self.flow.hass = self.hass
        
        # Вызываем async_step_scan без user_input
        result = await self.flow.async_step_scan()
        
        # Проверяем, что возвращается ошибка о ненайденном устройстве
        self.assertEqual(result['type'], 'abort')
        self.assertEqual(result['reason'], 'cooker_not_found')

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_scan_with_multiple_devices(self, mock_bluetooth):
        """Тест сканирования с несколькими устройствами."""
        # Создаем mock устройств
        supported_device = Mock()
        supported_device.address = "AA:BB:CC:DD:EE:FF"
        supported_device.name = "RMC-M40S"
        
        unsupported_device = Mock()
        unsupported_device.address = "11:22:33:44:55:66"
        unsupported_device.name = "Unknown_Device"
        
        # Создаем mock сканер
        mock_scanner = Mock()
        mock_scanner.discovered_devices = [supported_device, unsupported_device]
        mock_bluetooth.async_get_scanner.return_value = mock_scanner
        
        # Устанавливаем hass в flow
        self.flow.hass = self.hass
        
        # Вызываем async_step_scan без user_input
        result = await self.flow.async_step_scan()
        
        # Проверяем, что форма была показана с правильными данными
        self.assertEqual(result['type'], 'form')
        self.assertEqual(result['step_id'], 'scan')
        
        # Проверяем, что в схеме только поддерживаемое устройство
        schema = result['data_schema']
        mac_list = list(schema.schema['mac'].container.keys())
        self.assertEqual(len(mac_list), 1)
        self.assertIn("AA:BB:CC:DD:EE:FF (RMC-M40S)", mac_list)
        self.assertNotIn("11:22:33:44:55:66 (Unknown_Device)", mac_list)

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_scan_with_no_devices(self, mock_bluetooth):
        """Тест сканирования без устройств."""
        # Создаем mock сканер без устройств
        mock_scanner = Mock()
        mock_scanner.discovered_devices = []
        mock_bluetooth.async_get_scanner.return_value = mock_scanner
        
        # Устанавливаем hass в flow
        self.flow.hass = self.hass
        
        # Вызываем async_step_scan без user_input
        result = await self.flow.async_step_scan()
        
        # Проверяем, что возвращается ошибка о ненайденном устройстве
        self.assertEqual(result['type'], 'abort')
        self.assertEqual(result['reason'], 'cooker_not_found')

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_scan_with_bluetooth_error(self, mock_bluetooth):
        """Тест сканирования с ошибкой Bluetooth."""
        # Моделируем ошибку Bluetooth
        mock_bluetooth.async_get_scanner.side_effect = Exception("Bluetooth not available")
        
        # Устанавливаем hass в flow
        self.flow.hass = self.hass
        
        # Вызываем async_step_scan без user_input
        result = await self.flow.async_step_scan()
        
        # Проверяем, что возвращается ошибка о Bluetooth
        self.assertEqual(result['type'], 'abort')
        self.assertEqual(result['reason'], 'no_bluetooth')


if __name__ == '__main__':
    unittest.main()