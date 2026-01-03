#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import time
from datetime import datetime
from typing import Callable, Optional

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.components import bluetooth

from .const import SUPPORTED_DEVICES

_LOGGER = logging.getLogger(__name__)

# Стандартные UUID для R4S устройств (резервные)
DEFAULT_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
DEFAULT_NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
DEFAULT_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"


class BTLEConnection:
    def __init__(self, hass, mac, key):
        self.hass = hass
        self._mac = mac
        self._key = key
        self._client = None
        self._callbacks = {}
        self._connect_after = None
        self._type = None
        self._name = None
        self._available = False
        self._hex_iter = 0
        # Динамически определённые UUID
        self._service_uuid = None
        self._notify_uuid = None
        self._write_uuid = None

    async def setNameAndType(self):
        try:
            _LOGGER.debug("🔍 Поиск устройства по MAC-адресу: %s", self._mac)
            device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
            if device:
                self._name = device.name
                self._type = SUPPORTED_DEVICES.get(self._name, None)
                self._available = True
                _LOGGER.info("✅ Устройство найдено: %s, Тип: %s", self._name, self._type)
            else:
                self._available = False
                _LOGGER.warning("⚠️  Устройство не найдено по MAC-адресу: %s", self._mac)
        except Exception as e:
            _LOGGER.error("❌ Ошибка поиска устройства %s: %s", self._mac, e)
            self._available = False

    def setConnectAfter(self, callback: Callable):
        self._connect_after = callback

    def setCallback(self, command, callback: Callable):
        self._callbacks[str(command)] = callback

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        if self._client and self._client.is_connected:
            return

        try:
            _LOGGER.info("🔌 Подключение к устройству: %s", self._mac)
            device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
            if not device:
                raise BleakError(f"Device {self._mac} not found")
            
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                device,
                self._mac,
                max_attempts=3
            )
            _LOGGER.info("✅ Успешное подключение к %s", self._mac)
            
            # Автоматическое определение UUID сервисов и характеристик
            await self._discover_service_uuids()
            
            # Start notification с найденной характеристикой
            if self._notify_uuid:
                await self._client.start_notify(self._notify_uuid, self._notification_handler)
                _LOGGER.info("📡 Уведомления включены для %s через характеристику %s", self._mac, self._notify_uuid)
            else:
                _LOGGER.error("❌ Не удалось определить характеристику для уведомлений")
                raise BleakError("Notification characteristic not found")
            
            if self._connect_after:
                await self._connect_after()
                
        except Exception as e:
            _LOGGER.error("❌ Ошибка подключения к %s: %s", self._mac, e)
            await self.disconnect()
            raise

    async def disconnect(self):
        try:
            if self._client:
                if self._client.is_connected:
                    await self._client.disconnect()
                    _LOGGER.info("🔌 Отключение от устройства: %s", self._mac)
                self._client = None
        except Exception as e:
            _LOGGER.error("❌ Ошибка отключения от %s: %s", self._mac, e)

    def _notification_handler(self, sender, data):
        """Обработчик уведомлений от устройства."""
        try:
            _LOGGER.debug("📡 Получены данные от %s: %s", self._mac, data.hex())
            
            # Обработка данных по протоколу R4S
            if len(data) >= 4:
                command = data[2]
                if str(command) in self._callbacks:
                    self._callbacks[str(command)](data)
                else:
                    _LOGGER.debug("📡 Неизвестная команда: 0x%02x", command)
        except Exception as e:
            _LOGGER.error("❌ Ошибка обработки уведомления от %s: %s", self._mac, e)

    async def send_command(self, command, data=None):
        """Отправка команды устройству."""
        if not self._client or not self._client.is_connected:
            raise BleakError("Not connected to device")
        
        try:
            # Формирование пакета по протоколу R4S
            if data is None:
                data = []
            
            # Инкрементируем итератор
            self._hex_iter = (self._hex_iter + 1) % 256
            
            # Формируем пакет: [0x55, iter, command, data..., 0xAA]
            packet = [0x55, self._hex_iter, command] + data + [0xAA]
            packet_bytes = bytes(packet)
            
            _LOGGER.debug("📤 Отправка команды 0x%02x устройству %s: %s",
                         command, self._mac, packet_bytes.hex())
            
            # Используем найденную характеристику для записи
            if self._write_uuid:
                await self._client.write_gatt_char(self._write_uuid, packet_bytes)
                _LOGGER.debug("✅ Команда отправлена успешно через характеристику %s", self._write_uuid)
            else:
                _LOGGER.error("❌ Не удалось определить характеристику для записи")
                raise BleakError("Write characteristic not found")
            
        except Exception as e:
            _LOGGER.error("❌ Ошибка отправки команды 0x%02x устройству %s: %s",
                         command, self._mac, e)
            raise

    async def sendRequest(self, command, data=None):
        """Метод для совместимости с другими интеграциями - вызывает send_command."""
        # Конвертируем command в int
        if hasattr(command, 'value'):
            # Если это Enum (RedmondCommand), используем value
            command_int = int(str(command.value), 16)
        elif isinstance(command, str):
            # Если команда передана как строка в hex формате, конвертируем в int
            command_int = int(command, 16)
        else:
            command_int = command
        
        # Конвертируем data из hex строки в список байтов, если это строка
        if isinstance(data, str):
            data_list = [int(data[i:i+2], 16) for i in range(0, len(data), 2)]
        elif isinstance(data, list):
            data_list = data
        else:
            data_list = []
        
        return await self.send_command(command_int, data_list)

    async def _discover_service_uuids(self):
        """Автоматическое определение UUID сервисов и характеристик."""
        try:
            _LOGGER.debug("🔍 Поиск сервисов и характеристик для %s", self._mac)
            
            # Получаем все сервисы
            try:
                # Попробуем использовать get_services() как в оригинальном bleak
                services = await self._client.get_services()
            except AttributeError:
                # Если get_services() не доступен, используем services напрямую
                services = self._client.services
            
            # Подсчитываем количество сервисов
            service_count = len(list(services))
            _LOGGER.debug("📦 Найдено сервисов: %s", service_count)
            
            for service in services:
                _LOGGER.debug("📡 Сервис: %s", service.uuid)
                
                # Проверяем, является ли это Nordic UART Service
                if service.uuid.lower() == DEFAULT_SERVICE_UUID.lower():
                    self._service_uuid = service.uuid
                    _LOGGER.info("✅ Найден Nordic UART Service: %s", self._service_uuid)
                    
                    # Ищем характеристики для уведомлений и записи
                    for characteristic in service.characteristics:
                        _LOGGER.debug("📡 Характеристика: %s, свойства: %s",
                                    characteristic.uuid, characteristic.properties)
                        
                        if 'notify' in characteristic.properties:
                            self._notify_uuid = characteristic.uuid
                            _LOGGER.info("📢 Найдена характеристика для уведомлений: %s", self._notify_uuid)
                        
                        if 'write' in characteristic.properties or 'write-without-response' in characteristic.properties:
                            self._write_uuid = characteristic.uuid
                            _LOGGER.info("✏️  Найдена характеристика для записи: %s", self._write_uuid)
                    
                    # Если нашли все необходимые характеристики, выходим
                    if self._notify_uuid and self._write_uuid:
                        _LOGGER.info("✅ Все необходимые характеристики найдены для %s", self._mac)
                        return True
            
            # Если не нашли NUS, используем резервные UUID
            if not self._service_uuid:
                _LOGGER.warning("⚠️  Nordic UART Service не найден, используем резервные UUID")
                self._service_uuid = DEFAULT_SERVICE_UUID
                self._notify_uuid = DEFAULT_NOTIFY_UUID
                self._write_uuid = DEFAULT_WRITE_UUID
            
            return True
            
        except Exception as e:
            _LOGGER.error("❌ Ошибка определения UUID для %s: %s", self._mac, e)
            # В случае ошибки используем резервные UUID
            self._service_uuid = DEFAULT_SERVICE_UUID
            self._notify_uuid = DEFAULT_NOTIFY_UUID
            self._write_uuid = DEFAULT_WRITE_UUID
            return False

    async def send_auth(self):
        """Отправка команды аутентификации."""
        try:
            _LOGGER.info("🔑 Отправка команды аутентификации")
            
            # Конвертируем пароль в список байтов
            if isinstance(self._key, str):
                # Если пароль передан как hex строка, конвертируем в список байтов
                key_bytes = [int(self._key[i:i+2], 16) for i in range(0, len(self._key), 2)]
            elif isinstance(self._key, list):
                # Если пароль уже список байтов, используем как есть
                key_bytes = self._key
            else:
                # В других случаях пытаемся конвертировать
                key_bytes = list(self._key)
            
            _LOGGER.debug("🔑 Пароль для аутентификации: %s", key_bytes)
            await self.send_command(0x01, key_bytes)
        except Exception as e:
            _LOGGER.error("❌ Ошибка аутентификации: %s", e)
            raise

    async def send_status_request(self):
        """Запрос статуса устройства."""
        try:
            _LOGGER.debug("📊 Запрос статуса устройства")
            await self.send_command(0x02)
        except Exception as e:
            _LOGGER.error("❌ Ошибка запроса статуса: %s", e)
            raise

    @property
    def available(self):
        return self._available and self._client and self._client.is_connected

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def mac(self):
        return self._mac