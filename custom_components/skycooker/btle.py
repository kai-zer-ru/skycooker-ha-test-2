#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import time
from datetime import datetime
from typing import Callable, Optional

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

from .const import SUPPORTED_DEVICES

_LOGGER = logging.getLogger(__name__)

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID_WRITE = "0000fff2-0000-1000-8000-00805f9b34fb"


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
            device = await BleakScanner.find_device_by_address(self._mac)
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
            self._client = BleakClient(self._mac)
            await self._client.connect()
            _LOGGER.info("✅ Успешное подключение к %s", self._mac)

            # Start notification handler
            await self._client.start_notify(CHARACTERISTIC_UUID, self._notification_handler)
            _LOGGER.debug("📡 Обработчик уведомлений запущен")

            if self._connect_after:
                await self._connect_after(self)

        except BleakError as e:
            _LOGGER.error("❌ Ошибка подключения к %s: %s", self._mac, e)
            raise

    async def disconnect(self):
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            _LOGGER.debug("Disconnected from %s", self._mac)

    async def sendRequest(self, command, data=""):
        if not self._client or not self._client.is_connected:
            await self.connect()

        # Формируем пакет
        hex_iter = self.getHexNextIter()
        packet = f"55{hex_iter}{command}{data}aa"
        _LOGGER.debug("Sending packet: %s", packet)

        try:
            await self._client.write_gatt_char(CHARACTERISTIC_UUID_WRITE, bytes.fromhex(packet))
            return True
        except BleakError as e:
            _LOGGER.error("Failed to send request to %s: %s", self._mac, e)
            return False

    def _notification_handler(self, sender, data):
        """Обработчик уведомлений от устройства"""
        hex_data = data.hex()
        _LOGGER.debug("📡 Получено уведомление: %s", hex_data)

        # Проверяем формат пакета
        if len(hex_data) >= 6 and hex_data.startswith('55') and hex_data.endswith('aa'):
            # Извлекаем команду
            command = hex_data[4:6]
            _LOGGER.debug("📋 Команда: %s", command)

            # Вызываем callback если он есть
            if command in self._callbacks:
                try:
                    # Преобразуем hex строку в массив
                    arr_hex = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]
                    result = self._callbacks[command](arr_hex)
                    _LOGGER.debug("✅ Результат callback для команды %s: %s", command, result)
                except Exception as e:
                    _LOGGER.error("❌ Ошибка в callback для команды %s: %s", command, e)

    def getHexNextIter(self) -> str:
        self._hex_iter = (self._hex_iter + 1) % 256
        return f"{self._hex_iter:02x}"

    @staticmethod
    def hexToDec(hexChr: str) -> int:
        return int(hexChr, 16)

    @staticmethod
    def decToHex(num: int) -> str:
        return f"{num:02x}"