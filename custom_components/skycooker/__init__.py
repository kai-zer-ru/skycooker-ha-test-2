"""
Интеграция SkyCooker для Home Assistant.
Позволяет управлять мультиваркой Redmond RMC-M40S через Bluetooth.
"""

from __future__ import annotations

import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_DEVICE_TYPE, CONF_DEVICE_ADDRESS, CONF_DEVICE_NAME
from .logger import logger
from .multicooker import SkyCookerDevice

# Список поддерживаемых платформ
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка SkyCooker из конфигурационного входа."""
    logger.info("🔌 Настройка интеграции SkyCooker")
    
    # Initialize data structure / Инициализация структуры данных
    hass.data.setdefault(DOMAIN, {})
    
    # Create device instance / Создание экземпляра устройства
    device_type = entry.data[CONF_DEVICE_TYPE]
    device_address = entry.data[CONF_DEVICE_ADDRESS]
    device_name = entry.data[CONF_DEVICE_NAME]
    
    device = SkyCookerDevice(device_type, device_address, device_name, hass=hass, persistent=True)
    
    # Store device in hass data / Сохранение устройства в данных hass
    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
        "device_info": lambda: create_device_info(entry)
    }
    
    # Подключение к устройству
    connected = await device.connect()
    if not connected:
        logger.error("❌ Не удалось подключиться к устройству, прерывание настройки")
        return False
    
    # Передача настройки на все платформы
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Запуск периодического обновления статуса
    hass.async_create_task(periodic_status_update(hass, device))
    
    logger.success("✅ Настройка интеграции SkyCooker завершена")
    return True

async def periodic_status_update(hass: HomeAssistant, device: SkyCookerDevice):
    """Периодическое обновление статуса устройства."""
    while True:
        try:
            await device.get_status()
            await asyncio.sleep(30)  # Обновление каждые 30 секунд
        except Exception as e:
            logger.error(f"❌ Ошибка в периодическом обновлении статуса: {e}")
            await asyncio.sleep(60)  # Подождать дольше в случае ошибки

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Выгрузка конфигурационного входа."""
    logger.info("🔌 Выгрузка интеграции SkyCooker")
    
    # Получение устройства и отключение
    device = hass.data[DOMAIN][entry.entry_id]["device"]
    await device.disconnect()
    
    # Выгрузка всех платформ
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        logger.success("✅ Интеграция SkyCooker успешно выгружена")
    
    return unload_ok

def create_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Создание информации об устройстве для мультиварки."""
    return DeviceInfo(
        name=f"SkyCooker {entry.data[CONF_DEVICE_NAME]}",
        manufacturer="Redmond",
        model=entry.data[CONF_DEVICE_TYPE],
        identifiers={(DOMAIN, entry.data[CONF_DEVICE_ADDRESS])},
        connections={("bluetooth", entry.data[CONF_DEVICE_ADDRESS])}
    )