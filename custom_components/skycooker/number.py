#!/usr/local/bin/python3
# coding: utf-8

import logging
from typing import Any, Dict, Optional

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.const import CONF_MAC, CONF_PASSWORD, CONF_SCAN_INTERVAL, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_USE_BACKLIGHT,
    DOMAIN,
    SIGNAL_UPDATE_DATA,
    MIN_TEMP,
    MAX_TEMP,
)

_LOGGER = logging.getLogger(__name__)

NUMBER_TYPES = {
    "target_temperature": {
        "name": "Target Temperature",
        "icon": "mdi:thermometer",
        "device_class": NumberDeviceClass.TEMPERATURE,
        "unit_of_measurement": UnitOfTemperature.CELSIUS,
        "min_value": MIN_TEMP,
        "max_value": MAX_TEMP,
        "step": 1,
        "mode": NumberMode.SLIDER,
    },
    "program_hours": {
        "name": "Program Hours",
        "icon": "mdi:clock-outline",
        "device_class": None,
        "unit_of_measurement": "h",
        "min_value": 0,
        "max_value": 23,
        "step": 1,
        "mode": NumberMode.SLIDER,
    },
    "program_minutes": {
        "name": "Program Minutes",
        "icon": "mdi:clock-outline",
        "device_class": None,
        "unit_of_measurement": "min",
        "min_value": 0,
        "max_value": 59,
        "step": 1,
        "mode": NumberMode.SLIDER,
    },
    "timer_hours": {
        "name": "Timer Hours",
        "icon": "mdi:timer-outline",
        "device_class": None,
        "unit_of_measurement": "h",
        "min_value": 0,
        "max_value": 23,
        "step": 1,
        "mode": NumberMode.SLIDER,
    },
    "timer_minutes": {
        "name": "Timer Minutes",
        "icon": "mdi:timer-outline",
        "device_class": None,
        "unit_of_measurement": "min",
        "min_value": 0,
        "max_value": 59,
        "step": 1,
        "mode": NumberMode.SLIDER,
    },
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the SkyCooker number platform."""
    cooker = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for number_type in NUMBER_TYPES:
        entities.append(SkyCookerNumber(cooker, number_type))
    
    async_add_entities(entities)


class SkyCookerNumber(NumberEntity):
    """Representation of a SkyCooker number."""

    def __init__(self, cooker, number_type):
        """Initialize the number."""
        self._cooker = cooker
        self._number_type = number_type
        self._attr_name = f"{cooker._name} {NUMBER_TYPES[number_type]['name']}"
        self._attr_unique_id = f"{cooker._mac}_{number_type}"
        self._attr_icon = NUMBER_TYPES[number_type]["icon"]
        self._attr_device_class = NUMBER_TYPES[number_type]["device_class"]
        self._attr_unit_of_measurement = NUMBER_TYPES[number_type]["unit_of_measurement"]
        self._attr_native_min_value = NUMBER_TYPES[number_type]["min_value"]
        self._attr_native_max_value = NUMBER_TYPES[number_type]["max_value"]
        self._attr_native_step = NUMBER_TYPES[number_type]["step"]
        self._attr_mode = NUMBER_TYPES[number_type]["mode"]

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE_DATA, self._async_update
            )
        )

    @callback
    def _async_update(self):
        """Update number."""
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the current value."""
        if self._number_type == "target_temperature":
            return self._cooker._tgtemp
        elif self._number_type == "program_hours":
            return self._cooker._ph
        elif self._number_type == "program_minutes":
            return self._cooker._pm
        elif self._number_type == "timer_hours":
            return self._cooker._th
        elif self._number_type == "timer_minutes":
            return self._cooker._tm
        
        return None

    async def async_set_native_value(self, value):
        """Set new value."""
        if self._number_type == "target_temperature":
            await self._cooker.setTemperatureHeat(int(value))
        elif self._number_type == "program_hours":
            # Для изменения времени программы нужно перезапустить программу
            pass
        elif self._number_type == "program_minutes":
            # Для изменения времени программы нужно перезапустить программу
            pass
        elif self._number_type == "timer_hours":
            await self._cooker.modeTimeCook(f"{int(value):02x}", f"{self._cooker._tm:02x}")
        elif self._number_type == "timer_minutes":
            await self._cooker.modeTimeCook(f"{self._cooker._th:02x}", f"{int(value):02x}")

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