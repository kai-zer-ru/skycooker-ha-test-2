"""
Sensor platform for SkyCooker integration.
"""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .logger import logger
from .multicooker import SkyCookerDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SkyCooker sensors."""
    logger.sensor("🌡️ Setting up SkyCooker sensors")
    
    # Get device from hass data
    device = hass.data[DOMAIN][entry.entry_id]["device"]
    
    # Create sensors
    sensors = [
        SkyCookerStatusSensor(device),
        SkyCookerPowerSensor(device),
        SkyCookerProgramSensor(device),
        SkyCookerTemperatureSensor(device),
        SkyCookerTotalTimeSensor(device),
        SkyCookerRemainingTimeSensor(device),
        SkyCookerAutoWarmTimeSensor(device),
        SkyCookerCommandSuccessRateSensor(device),
        SkyCookerDelayedStartTimeSensor(device),
    ]
    
    async_add_entities(sensors)
    logger.success("✅ SkyCooker sensors setup complete")

class SkyCookerSensor(CoordinatorEntity, SensorEntity):
    """Base class for SkyCooker sensors."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the sensor."""
        super().__init__(device)
        self._device = device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.device_address)},
            "name": device.device_name,
            "manufacturer": "Redmond",
            "model": device.device_type,
        }
        self._attr_unique_id = f"{device.device_address}_{self._attr_name}"

class SkyCookerStatusSensor(SkyCookerSensor):
    """Sensor for displaying current status."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the status sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Status"
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._device.status_data:
            return self._device.status_data.get("status_text", "Unknown")
        return "Unknown"

class SkyCookerPowerSensor(SkyCookerSensor):
    """Binary sensor for power state."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the power sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Power"
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._device.status_data:
            status = self._device.status_data.get("status", 0)
            return "On" if status != 0 else "Off"
        return "Off"

class SkyCookerProgramSensor(SkyCookerSensor):
    """Sensor for displaying current program."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the program sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Program"
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._device.status_data:
            return self._device.status_data.get("mode_name", "Unknown")
        return "Unknown"

class SkyCookerTemperatureSensor(SkyCookerSensor):
    """Sensor for displaying current temperature."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the temperature sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Temperature"
        self._attr_native_unit_of_measurement = "°C"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._device.status_data:
            return self._device.status_data.get("temperature", 0)
        return 0

class SkyCookerTotalTimeSensor(SkyCookerSensor):
    """Sensor for displaying total program time."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the total time sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Total Time"
        self._attr_native_unit_of_measurement = "min"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._device.status_data:
            return self._device.status_data.get("time_total", 0)
        return 0

class SkyCookerRemainingTimeSensor(SkyCookerSensor):
    """Sensor for displaying remaining time."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the remaining time sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Remaining Time"
        self._attr_native_unit_of_measurement = "min"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._device.status_data:
            return self._device.status_data.get("remaining_time_total", 0)
        return 0

class SkyCookerAutoWarmTimeSensor(SkyCookerSensor):
    """Sensor for displaying auto warm time."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the auto warm time sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Auto Warm Time"
        self._attr_native_unit_of_measurement = "min"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._device.status_data:
            # Auto warm time is shown in remaining_time_total when in auto warm mode
            status = self._device.status_data.get("status", 0)
            if status == self._device.constants["STATUS_AUTO_WARM"]:
                return self._device.status_data.get("remaining_time_total", 0)
        return 0

class SkyCookerCommandSuccessRateSensor(SkyCookerSensor):
    """Sensor for displaying command success rate."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the command success rate sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Command Success Rate"
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return round(self._device.command_success_rate, 1)

class SkyCookerDelayedStartTimeSensor(SkyCookerSensor):
    """Sensor for displaying delayed start time."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the delayed start time sensor."""
        super().__init__(device)
        self._attr_name = f"{device.device_name} Delayed Start Time"
        self._attr_native_unit_of_measurement = "min"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._device.status_data:
            # Delayed start time is shown in remaining_time_total when in delayed launch mode
            status = self._device.status_data.get("status", 0)
            if status == self._device.constants["STATUS_DELAYED_LAUNCH"]:
                return self._device.status_data.get("remaining_time_total", 0)
        return 0