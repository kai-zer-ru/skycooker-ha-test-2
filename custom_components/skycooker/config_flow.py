"""
Config flow for SkyCooker integration.
"""

import asyncio
from typing import Any
from bleak import BleakScanner, BleakError

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import selector

from .const import DOMAIN, SUPPORTED_DEVICES, CONF_DEVICE_TYPE, CONF_DEVICE_ADDRESS, CONF_DEVICE_NAME
from .logger import logger

class SkyCookerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SkyCooker."""
    
    VERSION = 1
    
    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices = []
        self._selected_device = None
        self._device_type = None
        self._device_address = None
        self._device_name = None
    
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Обработка начального шага."""
        logger.info("🔌 Запуск настройки SkyCooker")
        
        if user_input is not None:
            # Пользователь выбрал тип устройства
            self._device_type = user_input[CONF_DEVICE_TYPE]
            return await self.async_step_discovery()
        
        # Показываем выбор типа устройства
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_TYPE): selector({
                    "select": {
                        "options": SUPPORTED_DEVICES,
                        "mode": "dropdown",
                        "translation_key": "device_type"
                    }
                })
            }),
            description_placeholders={"devices": ", ".join(SUPPORTED_DEVICES)}
        )
    
    async def async_step_discovery(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Поиск доступных Bluetooth устройств."""
        logger.bluetooth("📡 Поиск Bluetooth устройств...")
        
        if user_input is not None:
            # Пользователь выбрал устройство
            self._device_address = user_input[CONF_DEVICE_ADDRESS]
            # Находим имя устройства по адресу
            for device in self._discovered_devices:
                if device["address"] == self._device_address:
                    self._device_name = device["name"]
                    break
            
            # Проверяем, не настроено ли устройство уже
            await self.async_set_unique_id(self._device_address)
            self._abort_if_unique_id_configured()
            
            return await self.async_step_confirm()
        
        # Scan for devices
        try:
            devices = await BleakScanner.discover(timeout=10.0)
            self._discovered_devices = []
            
            for device in devices:
                if device.name:
                    # Используем ту же логику что и в оригинальном сканере - ищем "RMC" в имени устройства
                    name_lower = device.name.lower()
                    if "rmc" in name_lower:
                        self._discovered_devices.append({
                            "address": device.address,
                            "name": device.name
                        })
            
            if not self._discovered_devices:
                logger.warning("⚠️ Устройства SkyCooker не найдены")
                return self.async_abort(reason="no_devices_found")
            
            # Показываем выбор устройства
            return self.async_show_form(
                step_id="discovery",
                data_schema=vol.Schema({
                    vol.Required(CONF_DEVICE_ADDRESS): selector({
                        "select": {
                            "options": [
                                {
                                    "value": device["address"],
                                    "label": f"{device['name']} ({device['address']})"
                                }
                                for device in self._discovered_devices
                            ],
                            "mode": "dropdown",
                            "translation_key": "device_address"
                        }
                    })
                }),
                description_placeholders={"devices": len(self._discovered_devices)}
            )
            
        except BleakError as e:
            logger.error(f"❌ Ошибка поиска Bluetooth: {e}")
            return self.async_abort(reason="bluetooth_error")
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка поиска: {e}")
            return self.async_abort(reason="discovery_error")
    
    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Подтверждение выбора устройства."""
        logger.info("ℹ️ Пожалуйста, переведите ваше устройство в режим сопряжения")
        
        if user_input is not None:
            # Пользователь подтвердил, создаем запись конфигурации
            return self.async_create_entry(
                title=f"SkyCooker {self._device_type}",
                data={
                    CONF_DEVICE_TYPE: self._device_type,
                    CONF_DEVICE_ADDRESS: self._device_address,
                    CONF_DEVICE_NAME: self._device_name
                }
            )
        
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "device_name": self._device_name,
                "device_address": self._device_address
            }
        )
    
    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Обработка переконфигурации."""
        logger.info("🔧 Переконфигурация SkyCooker")
        return await self.async_step_user(user_input)

from homeassistant.helpers import config_validation as cv
import voluptuous as vol