#!/usr/bin/env python3
"""
Тестирование загрузки сущностей интеграции.
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к интеграции
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Имитируем HomeAssistant окружение
class MockHass:
    def __init__(self):
        self.data = {}
        self._signal_callbacks = {}
        
    def async_create_task(self, coro):
        return asyncio.create_task(coro)
        
    def config_entries(self):
        return MockConfigEntries()
        
    def dispatcher_connect(self, signal, callback):
        if signal not in self._signal_callbacks:
            self._signal_callbacks[signal] = []
        self._signal_callbacks[signal].append(callback)
        return lambda: self._signal_callbacks[signal].remove(callback)

class MockConfigEntries:
    def async_forward_entry_setup(self, config_entry, component):
        print(f"✅ Загрузка компонента: {component}")
        return True
        
    def async_forward_entry_unload(self, config_entry, component):
        print(f"✅ Выгрузка компонента: {component}")
        return True

class MockConfigEntry:
    def __init__(self):
        self.entry_id = "test_entry_id"
        self.unique_id = "test_unique_id"
        self.data = {
            "mac": "DA:D8:9F:9E:0B:4C",
            "password": "5b5b12868d0e8d12",
            "scan_interval": 30,
            "use_backlight": False
        }

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_entities_loading():
    """Тестирование загрузки сущностей."""
    logger.info("🚀 Тестирование загрузки сущностей")
    
    try:
        # Имитируем HomeAssistant
        hass = MockHass()
        
        # Создаем mock config_entry
        config_entry = MockConfigEntry()
        
        # Тестируем загрузку sensor
        logger.info("🧪 Тест загрузки sensor...")
        from custom_components.skycooker.sensor import async_setup_entry as sensor_setup
        await sensor_setup(hass, config_entry, lambda entities: logger.info(f"✅ Загружено sensor сущностей: {len(entities)}"))
        logger.info("✅ Загрузка sensor прошла успешно")
        
        # Тестируем загрузку switch
        logger.info("🧪 Тест загрузки switch...")
        from custom_components.skycooker.switch import async_setup_entry as switch_setup
        await switch_setup(hass, config_entry, lambda entities: logger.info(f"✅ Загружено switch сущностей: {len(entities)}"))
        logger.info("✅ Загрузка switch прошла успешно")
        
        # Тестируем загрузку number
        logger.info("🧪 Тест загрузки number...")
        from custom_components.skycooker.number import async_setup_entry as number_setup
        await number_setup(hass, config_entry, lambda entities: logger.info(f"✅ Загружено number сущностей: {len(entities)}"))
        logger.info("✅ Загрузка number прошла успешно")
        
        # Тестируем загрузку select
        logger.info("🧪 Тест загрузки select...")
        from custom_components.skycooker.select import async_setup_entry as select_setup
        await select_setup(hass, config_entry, lambda entities: logger.info(f"✅ Загружено select сущностей: {len(entities)}"))
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