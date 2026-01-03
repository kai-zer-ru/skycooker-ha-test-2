#!/usr/bin/env python3
# coding: utf-8

"""Тест для проверки обработки выбора устройства пользователем."""

import unittest
from unittest.mock import Mock, patch, AsyncMock
from custom_components.skycooker.config_flow import SkyCookerConfigFlow
from custom_components.skycooker.const import SUPPORTED_DEVICES, DOMAIN


class TestConfigFlowUserSelection(unittest.TestCase):
    """Тесты для проверки обработки выбора устройства."""

    def setUp(self):
        """Настройка теста."""
        self.hass = Mock()
        self.flow = SkyCookerConfigFlow()

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_user_selection_valid_device(self, mock_bluetooth):
        """Тест выбора поддерживаемого устройства."""
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
        
        # Сначала вызываем async_step_scan для получения формы
        result = await self.flow.async_step_scan()
        
        # Проверяем, что форма была показана
        self.assertEqual(result['type'], 'form')
        self.assertEqual(result['step_id'], 'scan')
        
        # Теперь имитируем выбор устройства пользователем
        user_input = {
            'mac': 'DA:D8:9F:9E:0B:4C (RMC-M40S)'
        }
        
        # Мокаем init_mac для успешного завершения
        with patch.object(self.flow, 'init_mac', return_value=AsyncMock(return_value=True)):
            result = await self.flow.async_step_scan(user_input)
        
        # Проверяем, что переход происходит на следующий шаг
        self.assertEqual(result['type'], 'form')
        self.assertEqual(result['step_id'], 'parameters')

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_user_selection_unsupported_device(self, mock_bluetooth):
        """Тест выбора неподдерживаемого устройства."""
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
        
        # Сначала вызываем async_step_scan для получения формы
        result = await self.flow.async_step_scan()
        
        # Проверяем, что форма была показана
        self.assertEqual(result['type'], 'form')
        self.assertEqual(result['step_id'], 'scan')
        
        # Теперь имитируем выбор устройства пользователем
        user_input = {
            'mac': 'AA:BB:CC:DD:EE:FF (Unknown_Device)'
        }
        
        result = await self.flow.async_step_scan(user_input)
        
        # Проверяем, что возвращается ошибка о неподдерживаемом устройстве
        self.assertEqual(result['type'], 'abort')
        self.assertEqual(result['reason'], 'unsupported_device')

    @patch('custom_components.skycooker.config_flow.bluetooth')
    async def test_user_selection_malformed_input(self, mock_bluetooth):
        """Тест обработки неправильного формата ввода."""
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
        
        # Сначала вызываем async_step_scan для получения формы
        result = await self.flow.async_step_scan()
        
        # Проверяем, что форма была показана
        self.assertEqual(result['type'], 'form')
        self.assertEqual(result['step_id'], 'scan')
        
        # Теперь имитируем выбор устройства пользователем с неправильным форматом
        user_input = {
            'mac': 'DA:D8:9F:9E:0B:4C'  # Без имени в скобках
        }
        
        result = await self.flow.async_step_scan(user_input)
        
        # Проверяем, что переход происходит на следующий шаг (устройство без имени)
        self.assertEqual(result['type'], 'form')
        self.assertEqual(result['step_id'], 'parameters')

    async def test_user_selection_exception_handling(self):
        """Тест обработки исключений при выборе устройства."""
        # Мокаем init_mac для выброса исключения
        with patch.object(self.flow, 'init_mac', side_effect=Exception("Test error")):
            user_input = {
                'mac': 'DA:D8:9F:9E:0B:4C (RMC-M40S)'
            }
            
            result = await self.flow.async_step_scan(user_input)
            
            # Проверяем, что возвращается ошибка
            self.assertEqual(result['type'], 'abort')
            self.assertEqual(result['reason'], 'unknown')


if __name__ == '__main__':
    unittest.main()