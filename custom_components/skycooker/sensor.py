#!/usr/local/bin/python3
# coding: utf-8

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfPower,
)
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
    MODE_MANUAL,
    MODE_AUTO,
    MIN_TEMP,
    MAX_TEMP,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "status": {
        "name": "Status",
        "icon": "mdi:state-machine",
        "device_class": None,
        "state_class": None,
    },
    "mode": {
        "name": "Mode",
        "icon": "mdi:stove",
        "device_class": None,
        "state_class": None,
    },
    "temperature": {
        "name": "Current Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": UnitOfTemperature.CELSIUS,
    },
    "target_temperature": {
        "name": "Target Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": UnitOfTemperature.CELSIUS,
    },
    "program_hours": {
        "name": "Program Hours",
        "icon": "mdi:clock-outline",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": UnitOfTime.HOURS,
    },
    "program_minutes": {
        "name": "Program Minutes",
        "icon": "mdi:clock-outline",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": UnitOfTime.MINUTES,
    },
    "timer_hours": {
        "name": "Timer Hours",
        "icon": "mdi:timer-outline",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": UnitOfTime.HOURS,
    },
    "timer_minutes": {
        "name": "Timer Minutes",
        "icon": "mdi:timer-outline",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": UnitOfTime.MINUTES,
    },
    "power_consumption": {
        "name": "Power Consumption",
        "icon": "mdi:flash",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": UnitOfPower.WATT,
    },
    "working_time": {
        "name": "Working Time",
        "icon": "mdi:clock-outline",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit_of_measurement": UnitOfTime.HOURS,
    },
    "starts_count": {
        "name": "Starts Count",
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit_of_measurement": "times",
    },
    "last_update": {
        "name": "Last Update",
        "icon": "mdi:update",
        "device_class": None,
        "state_class": None,
    },
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the SkyCooker sensor platform."""
    _LOGGER.info("🔧 Загрузка sensor платформы для %s", config_entry.entry_id)
    try:
        cooker = hass.data[DOMAIN][config_entry.entry_id]
        _LOGGER.info("✅ Найден cooker: %s", cooker._name)
        
        entities = []
        for sensor_type in SENSOR_TYPES:
            _LOGGER.info("🔧 Создание sensor сущности: %s", sensor_type)
            sensor = SkyCookerSensor(cooker, sensor_type)
            entities.append(sensor)
            _LOGGER.info("✅ Создана sensor сущность: %s", sensor.name)
        
        _LOGGER.info("🔧 Добавление %s sensor сущностей", len(entities))
        async_add_entities(entities)
        _LOGGER.info("✅ Загрузка sensor платформы завершена")
        return True
    except Exception as e:
        _LOGGER.error("❌ Ошибка загрузки sensor платформы: %s", e)
        _LOGGER.exception(e)
        return False


class SkyCookerSensor(SensorEntity):
    """Representation of a SkyCooker sensor."""

    def __init__(self, cooker, sensor_type):
        """Initialize the sensor."""
        self._cooker = cooker
        self._sensor_type = sensor_type
        self._attr_name = f"{cooker._name} {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unique_id = f"{cooker._mac}_{sensor_type}"
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]
        self._attr_state_class = SENSOR_TYPES[sensor_type]["state_class"]
        
        if "unit_of_measurement" in SENSOR_TYPES[sensor_type]:
            self._attr_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit_of_measurement"]

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE_DATA, self._async_update
            )
        )

    @callback
    def _async_update(self):
        """Update sensor."""
        self.async_write_ha_state()

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensor_type == "status":
            return self._get_status_text()
        elif self._sensor_type == "mode":
            return self._get_mode_text()
        elif self._sensor_type == "temperature":
            return self._cooker._temp
        elif self._sensor_type == "target_temperature":
            return self._cooker._tgtemp
        elif self._sensor_type == "program_hours":
            return self._cooker._ph
        elif self._sensor_type == "program_minutes":
            return self._cooker._pm
        elif self._sensor_type == "timer_hours":
            return self._cooker._th
        elif self._sensor_type == "timer_minutes":
            return self._cooker._tm
        elif self._sensor_type == "power_consumption":
            return self._cooker._Watts
        elif self._sensor_type == "working_time":
            return self._cooker._alltime
        elif self._sensor_type == "starts_count":
            return self._cooker._times
        elif self._sensor_type == "last_update":
            return self._cooker._time_upd
        
        return None

    def _get_status_text(self):
        """Get status text."""
        if self._cooker._status == STATUS_OFF:
            return "Выключено"
        elif self._cooker._status == STATUS_ON:
            return "Включено"
        elif self._cooker._status == COOKER_STATUS_PROGRAM:
            return "Программа"
        elif self._cooker._status == COOKER_STATUS_KEEP_WARM:
            return "Поддержание температуры"
        elif self._cooker._status == COOKER_STATUS_DELAYED_START:
            return "Отложенный старт"
        return "Неизвестно"

    def _get_mode_text(self):
        """Get mode text."""
        if self._cooker._mode == MODE_MANUAL:
            return "Ручной"
        elif self._cooker._mode == MODE_AUTO:
            return "Автоматический"
        return "Неизвестно"

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