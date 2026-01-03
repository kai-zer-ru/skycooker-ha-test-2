#!/usr/bin/env python3
"""
Простой тест интеграции skycooker.
Проверяет, что все ошибки исправлены.
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к интеграции
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.skycooker.btle import BTLEConnection

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_integration():
    """Тестирование интеграции."""
    logger.info("🚀 Тестирование интеграции skycooker")
    
    # MAC-адрес устройства
    mac_address = "DA:D8:9F:9E:0B:4C"
    
    # Пароль
    password = "5b5b12868d0e8d12"
    
    try:
        # Создаем соединение
        logger.info("🔌 Создание соединения с %s", mac_address)
        conn = BTLEConnection(None, mac_address, password)
        
        # Подключаемся
        logger.info("🔗 Подключение к устройству...")
        await conn.connect()
        logger.info("✅ Подключение успешно")
        
        # Проверяем, что соединение активно
        if conn.available:
            logger.info("✅ Соединение активно")
        else:
            logger.error("❌ Соединение не активно")
            return False
        
        # Тестируем отправку команды аутентификации
        logger.info("🔑 Отправка команды аутентификации...")
        await conn.send_auth()
        logger.info("✅ Команда аутентификации отправлена")
        
        # Тестируем отправку команды статуса (команда 0x02)
        logger.info("📊 Отправка команды статуса...")
        await conn.send_status_request()
        logger.info("✅ Команда статуса отправлена")
        
        # Ждём немного для получения ответов
        logger.info("⏳ Ожидание ответов...")
        await asyncio.sleep(2)
        
        # Отключаемся
        logger.info("🔌 Отключение от устройства...")
        await conn.disconnect()
        logger.info("✅ Отключение успешно")
        
        logger.info("🎉 Все тесты пройдены успешно!")
        return True
        
    except Exception as e:
        logger.error("❌ Ошибка при тестировании интеграции: %s", e)
        logger.exception(e)
        return False

async def main():
    """Основная функция."""
    success = await test_integration()
    if success:
        logger.info("✅ Интеграция работает корректно!")
        sys.exit(0)
    else:
        logger.error("❌ Интеграция содержит ошибки!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())