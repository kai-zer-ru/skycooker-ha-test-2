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

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID_WRITE = "0000fff1-0000-1000-8000-00805f9b34fb"


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
            
            # Find the correct characteristic for notifications
            services = await self._client.get_services()
            characteristic_uuid = None
            
            for service in services:
                if service.uuid == SERVICE_UUID:
                    for characteristic in service.characteristics:
                        if "notify" in characteristic.properties:
                            characteristic_uuid = characteristic.uuid
                            break
            
            if characteristic_uuid:
                # Start notification
                await self._client.start_notify(characteristic_uuid, self._notification_handler)
                _LOGGER.info("📡 Уведомления включены для %s через характеристику %s", self._mac, characteristic_uuid)
            else:
                _LOGGER.warning("⚠️  Не найдена характеристика для уведомлений, используем стандартную")
                await self._client.start_notify(CHARACTERISTIC_UUID, self._notification_handler)
            
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
            
            # Find the correct characteristic for writing
            services = await self._client.get_services()
            write_characteristic_uuid = None
            
            for service in services:
                if service.uuid == SERVICE_UUID:
                    for characteristic in service.characteristics:
                        if "write" in characteristic.properties or "write_without_response" in characteristic.properties:
                            write_characteristic_uuid = characteristic.uuid
                            break
            
            if write_characteristic_uuid:
                await self._client.write_gatt_char(write_characteristic_uuid, packet_bytes)
                _LOGGER.debug("✅ Команда отправлена успешно через характеристику %s", write_characteristic_uuid)
            else:
                _LOGGER.warning("⚠️  Не найдена характеристика для записи, используем стандартную")
                await self._client.write_gatt_char(CHARACTERISTIC_UUID, packet_bytes)
                _LOGGER.debug("✅ Команда отправлена успешно")
            
        except Exception as e:
            _LOGGER.error("❌ Ошибка отправки команды 0x%02x устройству %s: %s",
                         command, self._mac, e)
            raise

    async def send_auth(self):
        """Отправка команды аутентификации."""
        try:
            _LOGGER.info("🔑 Отправка команды аутентификации")
            await self.send_command(0x01, self._key)
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