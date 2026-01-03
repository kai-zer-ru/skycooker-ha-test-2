#!/usr/bin/env python3
"""
Тестирование импорта сущностей интеграции.
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к интеграции
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_entities_import():
    """Тестирование импорта сущностей."""
    logger.info("🚀 Тестирование импорта сущностей")
    
    try:
        # Тестируем импорт sensor
        logger.info("🧪 Тест импорта sensor...")
        from custom_components.skycooker.sensor import SkyCookerSensor
        logger.info("✅ Импорт sensor прошёл успешно")
        
        # Тестируем импорт switch
        logger.info("🧪 Тест импорта switch...")
        from custom_components.skycooker.switch import SkyCookerSwitch
        logger.info("✅ Импорт switch прошёл успешно")
        
        # Тестируем импорт number
        logger.info("🧪 Тест импорта number...")
        from custom_components.skycooker.number import SkyCookerNumber
        logger.info("✅ Импорт number прошёл успешно")
        
        # Тестируем импорт select
        logger.info("🧪 Тест импорта select...")
        from custom_components.skycooker.select import SkyCookerSelect
        logger.info("✅ Импорт select прошёл успешно")
        
        logger.info("🎉 Все сущности импортируются успешно!")
        return True
        
    except Exception as e:
        logger.error("❌ Ошибка при импорте сущностей: %s", e)
        logger.exception(e)
        return False

async def main():
    """Основная функция."""
    success = await test_entities_import()
    if success:
        logger.info("✅ Все сущности работают корректно!")
        sys.exit(0)
    else:
        logger.error("❌ Обнаружены проблемы с сущностями!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())