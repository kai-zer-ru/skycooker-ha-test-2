#!/usr/local/bin/python3
# coding: utf-8

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_MAC, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_USE_BACKLIGHT,
    DOMAIN,
    SIGNAL_UPDATE_DATA,
    STATUS_OFF,
    STATUS_ON,
    COOKER_STATUS_PROGRAM,
    COOKER_STATUS_KEEP_WARM,
    COOKER_STATUS_DELAYED_START,
)

_LOGGER = logging.getLogger(__name__)

SWITCH_TYPES = {
    "power": {
        "name": "Power",
        "icon": "mdi:power",
    },
    "program": {
        "name": "Program",
        "icon": "mdi:stove",
    },
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the SkyCooker switch platform."""
    _LOGGER.info("🔧 Загрузка switch платформы для %s", config_entry.entry_id)
    try:
        cooker = hass.data[DOMAIN][config_entry.entry_id]
        _LOGGER.info("✅ Найден cooker: %s", cooker._name)
        
        entities = []
        for switch_type in SWITCH_TYPES:
            _LOGGER.info("🔧 Создание switch сущности: %s", switch_type)
            switch = SkyCookerSwitch(cooker, switch_type)
            entities.append(switch)
            _LOGGER.info("✅ Создана switch сущность: %s", switch.name)
        
        _LOGGER.info("🔧 Добавление %s switch сущностей", len(entities))
        async_add_entities(entities)
        _LOGGER.info("✅ Загрузка switch платформы завершена")
        return True
    except Exception as e:
        _LOGGER.error("❌ Ошибка загрузки switch платформы: %s", e)
        _LOGGER.exception(e)
        return False


class SkyCookerSwitch(SwitchEntity):
    """Representation of a SkyCooker switch."""

    def __init__(self, cooker, switch_type):
        """Initialize the switch."""
        self._cooker = cooker
        self._switch_type = switch_type
        self._attr_name = f"{cooker._name} {SWITCH_TYPES[switch_type]['name']}"
        self._attr_unique_id = f"{cooker._mac}_{switch_type}"
        self._attr_icon = SWITCH_TYPES[switch_type]["icon"]

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE_DATA, self._async_update
            )
        )

    @callback
    def _async_update(self):
        """Update switch."""
        _LOGGER.debug("🔌 Обновление переключателя: %s", self._attr_name)
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Return true if switch is on."""
        if self._switch_type == "power":
            return self._cooker._status != STATUS_OFF
        elif self._switch_type == "program":
            return self._cooker._status in [COOKER_STATUS_PROGRAM, COOKER_STATUS_KEEP_WARM, COOKER_STATUS_DELAYED_START]
        
        return False

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if self._switch_type == "power":
            _LOGGER.info("🔌 Включение питания мультиварки")
            await self._cooker.modeOff()  # Сначала выключаем
            await self._cooker.modeOnCook(
                '01', '00', '64', '00', '23', '00', '00', '01'
            )  # Запускаем программу "Рис"
            _LOGGER.info("✅ Питание мультиварки включено")
        elif self._switch_type == "program":
            _LOGGER.info("🍲 Запуск программы приготовления")
            await self._cooker.modeOnCook(
                '01', '00', '64', '00', '23', '00', '00', '01'
            )  # Запускаем программу "Рис"
            _LOGGER.info("✅ Программа приготовления запущена")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if self._switch_type in ["power", "program"]:
            _LOGGER.info("🔌 Выключение мультиварки")
            await self._cooker.modeOff()
            _LOGGER.info("✅ Мультиварка выключена")

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._cooker._mac)},
            "name": self._cooker._name,
            "manufacturer": "Redmond",
            "model": self._cooker._name,
            "sw_version": self._cooker._firmware_ver,
        }

    @property
    def available(self):
        """Return True if entity is available."""
        return self._cooker._available