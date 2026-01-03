#!/usr/bin/env python3
# coding: utf-8

"""
Скрипт для тестирования аутентификации мультиварки RMC-M40S
Использует только bleak, без зависимостей от HomeAssistant
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Константы
MAC_ADDRESS = "DA:D8:9F:9E:0B:4C"  # Замените на MAC-адрес вашего устройства
PASSWORD = "5b5b12868d0e8d12"  # Пример пароля в hex формате (16 символов)

# UUID для Nordic UART Service
SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"


class SimpleBTLEConnection:
    """Упрощённое соединение с устройством для тестирования."""
    
    def __init__(self, mac, password):
        self._mac = mac
        self._password = password
        self._client = None
        self._hex_iter = 0
        self._auth_result = None
        
    async def connect(self):
        """Подключение к устройству."""
        from bleak import BleakClient
        
        logger.info("🔌 Подключение к устройству: %s", self._mac)
        self._client = BleakClient(self._mac)
        await self._client.connect()
        logger.info("✅ Успешное подключение к %s", self._mac)
        
        # Включаем уведомления
        await self._client.start_notify(NOTIFY_UUID, self._notification_handler)
        logger.info("📡 Уведомления включены через характеристику %s", NOTIFY_UUID)
        
    async def disconnect(self):
        """Отключение от устройства."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            logger.info("🔌 Отключение от устройства: %s", self._mac)
            
    def _notification_handler(self, sender, data):
        """Обработчик уведомлений."""
        logger.debug("📡 Получены данные: %s", data.hex())
        
        # Обработка ответа на аутентификацию
        if len(data) >= 4 and data[2] == 0x01:  # Команда аутентификации
            auth_result = data[3]
            logger.info("🔑 Результат аутентификации: 0x%02x", auth_result)
            if auth_result == 0x01:
                logger.info("✅ Аутентификация успешна!")
                self._auth_result = True
            else:
                logger.warning("⚠️  Аутентификация не удалась, код: 0x%02x", auth_result)
                self._auth_result = False
                
    async def send_auth(self):
        """Отправка команды аутентификации."""
        logger.info("🔑 Отправка команды аутентификации")
        logger.debug("🔑 Пароль: %s (тип: %s)", self._password, type(self._password))
        
        # Конвертируем пароль в список байтов
        if isinstance(self._password, str):
            # Если пароль передан как hex строка, конвертируем в список байтов
            key_bytes = [int(self._password[i:i+2], 16) for i in range(0, len(self._password), 2)]
            logger.debug("🔑 Пароль конвертирован из hex строки: %s", key_bytes)
        elif isinstance(self._password, list):
            # Если пароль уже список байтов, используем как есть
            key_bytes = self._password
            logger.debug("🔑 Пароль уже список байтов: %s", key_bytes)
        else:
            # В других случаях пытаемся конвертировать
            key_bytes = list(self._password)
            logger.debug("🔑 Пароль конвертирован из другого типа: %s", key_bytes)
        
        # Проверяем длину пароля
        if len(key_bytes) != 8:
            logger.warning("⚠️  Неправильная длина пароля: %s (ожидается 8 байт)", len(key_bytes))
        
        # Формируем пакет: [0x55, iter, 0x01, password..., 0xAA]
        self._hex_iter = (self._hex_iter + 1) % 256
        packet = [0x55, self._hex_iter, 0x01] + key_bytes + [0xAA]
        packet_bytes = bytes(packet)
        
        logger.debug("📤 Отправка команды аутентификации: %s", packet_bytes.hex())
        await self._client.write_gatt_char(WRITE_UUID, packet_bytes)
        logger.debug("✅ Команда аутентификации отправлена")
        
    async def test_authentication(self):
        """Тестирование аутентификации."""
        try:
            await self.connect()
            
            # Отправляем команду аутентификации
            await self.send_auth()
            
            # Ждём ответа
            await asyncio.sleep(2)
            
            # Проверяем результат
            if self._auth_result is True:
                logger.info("🎉 Аутентификация прошла успешно!")
                return True
            elif self._auth_result is False:
                logger.error("❌ Аутентификация не удалась!")
                return False
            else:
                logger.warning("⚠️  Не получен ответ на аутентификацию")
                return False
                
        except Exception as e:
            logger.error("❌ Ошибка при аутентификации: %s", e)
            logger.exception(e)
            return False
        finally:
            await self.disconnect()


async def test_password_formats():
    """Тестирование различных форматов пароля."""
    logger.info("🔍 Тестирование различных форматов пароля")
    
    # Разные форматы пароля для тестирования
    test_passwords = [
        "5b5b12868d0e8d12",  # Hex строка (16 символов)
        [0x5b, 0x5b, 0x12, 0x86, 0x8d, 0x0e, 0x8d, 0x12],  # Список байтов
        [91, 91, 18, 134, 141, 14, 141, 18],  # Список десятичных чисел
        "5b5b12868d0e8d",  # Неправильная длина (14 символов)
        "5b5b12868d0e8d1233",  # Неправильная длина (18 символов)
    ]
    
    for i, password in enumerate(test_passwords):
        logger.info("🧪 Тест %d: %s (тип: %s)", i+1, password, type(password))
        
        connection = SimpleBTLEConnection(MAC_ADDRESS, password)
        result = await connection.test_authentication()
        
        if result:
            logger.info("✅ Тест %d прошёл успешно", i+1)
        else:
            logger.error("❌ Тест %d не удался", i+1)
        
        # Пауза между тестами
        await asyncio.sleep(1)


async def main():
    """Главная функция."""
    logger.info("🚀 Запуск тестирования аутентификации мультиварки")
    logger.info("📱 MAC-адрес устройства: %s", MAC_ADDRESS)
    
    # Тестируем основную аутентификацию
    connection = SimpleBTLEConnection(MAC_ADDRESS, PASSWORD)
    result = await connection.test_authentication()
    
    if result:
        logger.info("🎉 Основная аутентификация прошла успешно!")
    else:
        logger.error("❌ Основная аутентификация не удалась!")
    
    # Тестируем различные форматы пароля
    await test_password_formats()
    
    logger.info("🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main())