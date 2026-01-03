#!/usr/bin/env python3
"""
Тесты для проверки динамического определения UUID в BTLEConnection
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bleak import BleakClient
from custom_components.skycooker.btle import BTLEConnection
from custom_components.skycooker.const import SUPPORTED_DEVICES


class TestBTLEConnectionDiscovery:
    """Тесты для динамического определения UUID"""

    @pytest.fixture
    def mock_hass(self):
        """Мок для HomeAssistant"""
        return MagicMock()

    @pytest.fixture
    def mock_device(self):
        """Мок для Bluetooth устройства"""
        device = MagicMock()
        device.name = "RMC-M40S"
        return device

    @pytest.fixture
    def mock_client(self):
        """Мок для BleakClient"""
        client = MagicMock()
        client.is_connected = True
        client.get_services = AsyncMock()
        client.start_notify = AsyncMock()
        client.write_gatt_char = AsyncMock()
        return client

    @pytest.fixture
    def mock_service(self):
        """Мок для Bluetooth сервиса"""
        service = MagicMock()
        service.uuid = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
        return service

    @pytest.fixture
    def mock_notify_characteristic(self):
        """Мок для характеристики уведомлений"""
        char = MagicMock()
        char.uuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
        char.properties = ["notify"]
        return char

    @pytest.fixture
    def mock_write_characteristic(self):
        """Мок для характеристики записи"""
        char = MagicMock()
        char.uuid = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
        char.properties = ["write", "write-without-response"]
        return char

    async def test_discover_service_uuids_success(
        self, mock_hass, mock_device, mock_client,
        mock_service, mock_notify_characteristic, mock_write_characteristic
    ):
        """Тест успешного определения UUID"""
        # Настраиваем моки
        mock_service.characteristics = [
            mock_notify_characteristic,
            mock_write_characteristic
        ]
        mock_client.get_services.return_value = [mock_service]
        
        # Создаем соединение
        connection = BTLEConnection(mock_hass, "DA:D8:9F:9E:0B:4C", [0x00, 0x11, 0x22, 0x33])
        connection._client = mock_client
        
        # Выполняем определение UUID
        result = await connection._discover_service_uuids()
        
        # Проверяем результат
        assert result is True
        assert connection._service_uuid == "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
        assert connection._notify_uuid == "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
        assert connection._write_uuid == "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

    async def test_discover_service_uuids_fallback(
        self, mock_hass, mock_device, mock_client
    ):
        """Тест использования резервных UUID при отсутствии NUS"""
        # Настраиваем моки - сервис не является NUS
        mock_service = MagicMock()
        mock_service.uuid = "00001800-0000-1000-8000-00805f9b34fb"  # Generic Access Service
        mock_client.get_services.return_value = [mock_service]
        
        # Создаем соединение
        connection = BTLEConnection(mock_hass, "DA:D8:9F:9E:0B:4C", [0x00, 0x11, 0x22, 0x33])
        connection._client = mock_client
        
        # Выполняем определение UUID
        result = await connection._discover_service_uuids()
        
        # Проверяем результат - должны использоваться резервные UUID
        assert result is True
        assert connection._service_uuid == "6e400001-b5a3-f393-e0a9-e50e24dcca9e"  # DEFAULT_SERVICE_UUID
        assert connection._notify_uuid == "6e400003-b5a3-f393-e0a9-e50e24dcca9e"   # DEFAULT_NOTIFY_UUID
        assert connection._write_uuid == "6e400002-b5a3-f393-e0a9-e50e24dcca9e"    # DEFAULT_WRITE_UUID

    async def test_discover_service_uuids_error_handling(
        self, mock_hass, mock_device, mock_client
    ):
        """Тест обработки ошибок при определении UUID"""
        # Настраиваем моки - ошибка при получении сервисов
        mock_client.get_services.side_effect = Exception("Test error")
        
        # Создаем соединение
        connection = BTLEConnection(mock_hass, "DA:D8:9F:9E:0B:4C", [0x00, 0x11, 0x22, 0x33])
        connection._client = mock_client
        
        # Выполняем определение UUID
        result = await connection._discover_service_uuids()
        
        # Проверяем результат - должны использоваться резервные UUID
        assert result is False
        assert connection._service_uuid == "6e400001-b5a3-f393-e0a9-e50e24dcca9e"  # DEFAULT_SERVICE_UUID
        assert connection._notify_uuid == "6e400003-b5a3-f393-e0a9-e50e24dcca9e"   # DEFAULT_NOTIFY_UUID
        assert connection._write_uuid == "6e400002-b5a3-f393-e0a9-e50e24dcca9e"    # DEFAULT_WRITE_UUID

    async def test_connect_with_dynamic_uuids(
        self, mock_hass, mock_device, mock_client,
        mock_service, mock_notify_characteristic, mock_write_characteristic
    ):
        """Тест подключения с динамическим определением UUID"""
        # Настраиваем моки
        mock_service.characteristics = [
            mock_notify_characteristic,
            mock_write_characteristic
        ]
        mock_client.get_services.return_value = [mock_service]
        mock_client.start_notify = AsyncMock()
        
        # Мокаем bluetooth.async_ble_device_from_address
        with patch('custom_components.skycooker.btle.bluetooth.async_ble_device_from_address', return_value=mock_device):
            # Мокаем establish_connection
            with patch('custom_components.skycooker.btle.establish_connection', return_value=mock_client):
                # Создаем соединение
                connection = BTLEConnection(mock_hass, "DA:D8:9F:9E:0B:4C", [0x00, 0x11, 0x22, 0x33])
                
                # Подключаемся
                await connection.connect()
                
                # Проверяем, что UUID были определены
                assert connection._service_uuid == "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
                assert connection._notify_uuid == "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
                assert connection._write_uuid == "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
                
                # Проверяем, что start_notify был вызван с правильной характеристикой
                mock_client.start_notify.assert_called_once_with(
                    "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
                    connection._notification_handler
                )

    async def test_send_command_with_dynamic_uuids(
        self, mock_hass, mock_device, mock_client,
        mock_service, mock_notify_characteristic, mock_write_characteristic
    ):
        """Тест отправки команды с динамическими UUID"""
        # Настраиваем моки
        mock_service.characteristics = [
            mock_notify_characteristic,
            mock_write_characteristic
        ]
        mock_client.get_services.return_value = [mock_service]
        mock_client.write_gatt_char = AsyncMock()
        mock_client.is_connected = True
        
        # Создаем соединение
        connection = BTLEConnection(mock_hass, "DA:D8:9F:9E:0B:4C", [0x00, 0x11, 0x22, 0x33])
        connection._client = mock_client
        
        # Определяем UUID
        await connection._discover_service_uuids()
        
        # Отправляем команду
        await connection.send_command(0x01, [0x01, 0x02, 0x03])
        
        # Проверяем, что write_gatt_char был вызван с правильной характеристикой
        mock_client.write_gatt_char.assert_called_once()
        args, kwargs = mock_client.write_gatt_char.call_args
        
        # Проверяем, что первым аргументом была передана правильная характеристика
        assert args[0] == "6e400002-b5a3-f393-e0a9-e50e24dcca9e"