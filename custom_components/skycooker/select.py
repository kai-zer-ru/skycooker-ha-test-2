#!/usr/local/bin/python3
# coding: utf-8

import logging
from typing import Any, Dict, Optional, List

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_MAC, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_USE_BACKLIGHT,
    DOMAIN,
    SIGNAL_UPDATE_DATA,
    COOKER_PROGRAMS,
)

_LOGGER = logging.getLogger(__name__)

SELECT_TYPES = {
    "program": {
        "name": "Program",
        "icon": "mdi:stove",
    },
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the SkyCooker select platform."""
    _LOGGER.info("🔧 Загрузка select платформы для %s", config_entry.entry_id)
    try:
        cooker = hass.data[DOMAIN][config_entry.entry_id]
        _LOGGER.info("✅ Найден cooker: %s", cooker._name)
        
        entities = []
        for select_type in SELECT_TYPES:
            _LOGGER.info("🔧 Создание select сущности: %s", select_type)
            select = SkyCookerSelect(cooker, select_type)
            entities.append(select)
            _LOGGER.info("✅ Создана select сущность: %s", select.name)
        
        _LOGGER.info("🔧 Добавление %s select сущностей", len(entities))
        async_add_entities(entities)
        _LOGGER.info("✅ Загрузка select платформы завершена")
        return True
    except Exception as e:
        _LOGGER.error("❌ Ошибка загрузки select платформы: %s", e)
        _LOGGER.exception(e)
        return False


class SkyCookerSelect(SelectEntity):
    """Representation of a SkyCooker select."""

    def __init__(self, cooker, select_type):
        """Initialize the select."""
        self._cooker = cooker
        self._select_type = select_type
        self._attr_name = f"{cooker._name} {SELECT_TYPES[select_type]['name']}"
        self._attr_unique_id = f"{cooker._mac}_{select_type}"
        self._attr_icon = SELECT_TYPES[select_type]["icon"]
        self._attr_options = list(COOKER_PROGRAMS.keys())

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE_DATA, self._async_update
            )
        )

    @callback
    def _async_update(self):
        """Update select."""
        self.async_write_ha_state()

    @property
    def current_option(self):
        """Return the current option."""
        # Нужно определить текущую программу по кодам
        current_prog = self._cooker._prog
        current_sprog = self._cooker._sprog
        
        for program_name, program_data in COOKER_PROGRAMS.items():
            if program_data[0] == current_prog and program_data[1] == current_sprog:
                return program_name
        
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option in COOKER_PROGRAMS:
            program_data = COOKER_PROGRAMS[option]
            await self._cooker.modeOnCook(
                program_data[0],  # prog
                program_data[1],  # sprog
                program_data[2],  # temp
                program_data[3],  # hours
                program_data[4],  # minutes
                program_data[5],  # dhours
                program_data[6],  # dminutes
                program_data[7],  # heat
            )

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