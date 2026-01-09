"""SkyCooker sensors."""
import logging

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                              SensorStateClass)
from homeassistant.const import (CONF_FRIENDLY_NAME, PERCENTAGE, UnitOfTemperature,
                                  UnitOfTime)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory

from .const import *

_LOGGER = logging.getLogger(__name__)




async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker sensors."""
    async_add_entities([
        SkyCookerSensor(hass, entry, SENSOR_TYPE_STATUS),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_TEMPERATURE),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_REMAINING_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_TOTAL_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_AUTO_WARM_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_SUCCESS_RATE),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_DELAYED_LAUNCH_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_SW_VERSION),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_CURRENT_MODE),
    ])


class SkyCookerSensor(SensorEntity):
    """Representation of a SkyCooker sensor."""

    def __init__(self, hass, entry, sensor_type):
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self.sensor_type = sensor_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the sensor."""
        self.schedule_update_ha_state()

    @property
    def skycooker(self):
        """Get the skycooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.sensor_type}"

    @property
    def device_info(self):
        """Return device info."""
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def assumed_state(self):
        """Return true if unable to access real state of the entity."""
        return False

    @property
    def last_reset(self):
        """Return last reset."""
        return None

    @property
    def name(self):
        """Return the name of the sensor."""
        base_name = (SKYCOOKER_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()
        
        # Determine the language index (0 for English, 1 for Russian)
        language = self.hass.config.language
        is_russian = language == "ru"
        
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return f"{base_name} {'статус' if is_russian else 'status'}"
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return f"{base_name} {'температура' if is_russian else 'temperature'}"
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return f"{base_name} {'оставшееся время' if is_russian else 'remaining time'}"
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return f"{base_name} {'общее время' if is_russian else 'total time'}"
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return f"{base_name} {'время автоподогрева' if is_russian else 'auto warm time'}"
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return f"{base_name} {'процент успеха' if is_russian else 'success rate'}"
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            return f"{base_name} {'время до отложенного запуска' if is_russian else 'delayed launch time'}"
        elif self.sensor_type == SENSOR_TYPE_SW_VERSION:
            return f"{base_name} {'версия ПО' if is_russian else 'software version'}"
        elif self.sensor_type == SENSOR_TYPE_CURRENT_MODE:
            return f"{base_name} {'текущий режим' if is_russian else 'current mode'}"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return "mdi:information"
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return "mdi:thermometer"
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return "mdi:timer"
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return "mdi:clock"
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return "mdi:clock-start"
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return "mdi:bluetooth-connect"
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            return "mdi:timer-sand"
        elif self.sensor_type == SENSOR_TYPE_SW_VERSION:
            return "mdi:information-outline"
        elif self.sensor_type == SENSOR_TYPE_CURRENT_MODE:
            return "mdi:chef-hat"
        return None

    @property
    def available(self):
        """Return if sensor is available."""
        # If the skycooker is not available, return False
        if not self.skycooker.available:
            return False
         
        # For success rate, delayed launch time, and software version sensors, always return True if skycooker is available
        if self.sensor_type in [SENSOR_TYPE_SUCCESS_RATE, SENSOR_TYPE_DELAYED_LAUNCH_TIME, SENSOR_TYPE_SW_VERSION]:
            return True
         
        # For other sensors, check if we have data
        # But if skycooker is available, we should give it some time to get data
        # So we return True if skycooker is available, even if data is not yet available
        # This prevents sensors from becoming unavailable immediately after setup or connection issues
         
        # However, if we have never received any data for this sensor, we should return False
        # to indicate that the sensor is not yet ready
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return self.skycooker.status_code is not None
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return self.skycooker.target_temp is not None
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return self.skycooker.remaining_time is not None
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return self.skycooker.total_time is not None
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return self.skycooker.auto_warm_enabled is not None
        elif self.sensor_type == SENSOR_TYPE_CURRENT_MODE:
            return self.skycooker.current_mode is not None
        
        return False

    @property
    def entity_category(self):
        """Return entity category."""
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def device_class(self):
        """Return device class."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return SensorDeviceClass.TEMPERATURE
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_TOTAL_TIME, 
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return SensorDeviceClass.DURATION
        return None

    @property
    def state_class(self):
        """Return state class."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return SensorStateClass.MEASUREMENT
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_TOTAL_TIME, 
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return SensorStateClass.MEASUREMENT
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return SensorStateClass.MEASUREMENT
        return None

    @property
    def native_unit_of_measurement(self):
        """Return unit of measurement."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_TOTAL_TIME, 
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return UnitOfTime.MINUTES
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return PERCENTAGE
        return None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.sensor_type == SENSOR_TYPE_STATUS:
            status_code = self.skycooker.status_code
            if status_code is not None:
                # Determine the language index (0 for English, 1 for Russian)
                language = self.hass.config.language
                lang_index = 0 if language == "en" else 1
                return STATUS_CODES[lang_index].get(status_code, f"Unknown ({status_code})" if lang_index == 0 else f"Неизвестно ({status_code})")
            return "Unknown" if self.hass.config.language == "en" else "Неизвестно"
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return self.skycooker.target_temp if self.skycooker.target_temp is not None else 0
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return self.skycooker.remaining_time if self.skycooker.remaining_time is not None else 0
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return self.skycooker.total_time if self.skycooker.total_time is not None else 0
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            status_code = self.skycooker.status_code
            if status_code is not None:
                return self.skycooker.remaining_time if status_code == STATUS_AUTO_WARM else 0
            return 0
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return self.skycooker.success_rate if self.skycooker.success_rate is not None else 0
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            status_code = self.skycooker.status_code
            if status_code is not None:
                return self.skycooker.remaining_time if status_code == STATUS_DELAYED_LAUNCH else 0
            return 0
        elif self.sensor_type == SENSOR_TYPE_SW_VERSION:
            return self.skycooker.sw_version if self.skycooker.sw_version is not None else "Unknown"
        elif self.sensor_type == SENSOR_TYPE_CURRENT_MODE:
            current_mode = self.skycooker.current_mode
            if current_mode is not None:
                # Get the model type from the connection
                model_type = self.skycooker.model_code
                if model_type is None:
                    return f"Unknown ({current_mode})"
                
                # Get the mode names for the current model
                mode_names = MODE_NAMES.get(model_type, [None, None])
                if not mode_names or len(mode_names) < 2:
                    return f"Unknown ({current_mode})"
                
                # Determine the language index (0 for English, 1 for Russian)
                language = self.hass.config.language
                lang_index = 0 if language == "en" else 1
                
                if current_mode < len(mode_names[lang_index]):
                    return mode_names[lang_index][current_mode]
                return f"Unknown ({current_mode})"
            return "Unknown" if self.hass.config.language == "en" else "Неизвестно"
       
        return None