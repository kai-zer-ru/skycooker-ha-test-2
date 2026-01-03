#!/usr/bin/env python3
# coding: utf-8

"""
Скрипт для тестирования аутентификации мультиварки RMC-M40S
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к custom_components для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.skycooker.btle import BTLEConnection
from custom_components.skycooker.const import SUPPORTED_DEVICES

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Константы
MAC_ADDRESS = "DA:D8:9F:9E:0B:4C"  # Замените на MAC-адрес вашего устройства
PASSWORD = "5b5b12868d0e8d12"  # Пример пароля в hex формате (16 символов)


async def test_authentication():
    """Тестирование аутентификации устройства."""
    logger.info("🔍 Начало тестирования аутентификации")
    logger.info("📱 MAC-адрес устройства: %s", MAC_ADDRESS)
    logger.info("🔑 Пароль: %s", PASSWORD)
    
    try:
        # Создаем соединение
        connection = BTLEConnection(None, MAC_ADDRESS, PASSWORD)
        
        # Устанавливаем имя и тип устройства
        await connection.setNameAndType()
        logger.info("🏷️  Имя устройства: %s", connection.name)
        logger.info("🔧 Тип устройства: %s", connection.type)
        
        # Подключаемся к устройству
        async with connection:
            logger.info("✅ Успешное подключение к устройству")
            
            # Тестируем аутентификацию
            logger.info("🔑 Начало аутентификации...")
            await connection.send_auth()
            logger.info("✅ Аутентификация завершена")
            
            # Ждём немного для получения ответа
            await asyncio.sleep(2)
            
            logger.info("🎉 Тестирование аутентификации завершено успешно!")
            
    except Exception as e:
        logger.error("❌ Ошибка при тестировании аутентификации: %s", e)
        logger.exception(e)


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
        
        try:
            connection = BTLEConnection(None, MAC_ADDRESS, password)
            await connection.setNameAndType()
            
            async with connection:
                logger.info("✅ Подключение успешно для пароля: %s", password)
                await connection.send_auth()
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error("❌ Ошибка с паролем %s: %s", password, e)


async def main():
    """Главная функция."""
    logger.info("🚀 Запуск тестирования аутентификации мультиварки")
    
    # Тестируем основную аутентификацию
    await test_authentication()
    
    # Тестируем различные форматы пароля
    await test_password_formats()
    
    logger.info("🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main())