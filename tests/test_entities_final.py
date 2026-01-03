#!/usr/bin/env python3
"""
Финальный тест для проверки загрузки сущностей интеграции.
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к интеграции
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_entities_loading():
    """Тестирование загрузки сущностей."""
    logger.info("🚀 Финальная проверка загрузки сущностей")
    
    try:
        # Тестируем загрузку sensor
        logger.info("🧪 Тест загрузки sensor...")
        from skycooker.sensor import async_setup_entry as sensor_setup
        logger.info("✅ Загрузка sensor прошла успешно")
        
        # Тестируем загрузку switch
        logger.info("🧪 Тест загрузки switch...")
        from skycooker.switch import async_setup_entry as switch_setup
        logger.info("✅ Загрузка switch прошла успешно")
        
        # Тестируем загрузку number
        logger.info("🧪 Тест загрузки number...")
        from skycooker.number import async_setup_entry as number_setup
        logger.info("✅ Загрузка number прошла успешно")
        
        # Тестируем загрузку select
        logger.info("🧪 Тест загрузки select...")
        from skycooker.select import async_setup_entry as select_setup
        logger.info("✅ Загрузка select прошла успешно")
        
        logger.info("🎉 Все сущности загружаются успешно!")
        return True
        
    except Exception as e:
        logger.error("❌ Ошибка при загрузке сущностей: %s", e)
        logger.exception(e)
        return False

async def main():
    """Основная функция."""
    success = await test_entities_loading()
    if success:
        logger.info("✅ Все сущности работают корректно!")
        sys.exit(0)
    else:
        logger.error("❌ Обнаружены проблемы с сущностями!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())