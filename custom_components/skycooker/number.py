"""SkyCooker number entities."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import CONF_FRIENDLY_NAME, UnitOfTemperature, UnitOfTime
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker number entities."""
    async_add_entities([
        SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE),
        SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_HOURS),
        SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_MINUTES),
        SkyCookerNumber(hass, entry, NUMBER_TYPE_DELAYED_START_HOURS),
        SkyCookerNumber(hass, entry, NUMBER_TYPE_DELAYED_START_MINUTES),
    ])


class SkyCookerNumber(NumberEntity):
    """Representation of a SkyCooker number entity."""

    def __init__(self, hass, entry, number_type):
        """Initialize the number entity."""
        self.hass = hass
        self.entry = entry
        self.number_type = number_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the number entity."""
        self.schedule_update_ha_state()

    @property
    def skycooker(self):
        """Get the skycooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.number_type}"

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
    def name(self):
        """Return the name of the number entity."""
        base_name = (SKYCOOKER_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()
        
        # Determine the language index (0 for English, 1 for Russian)
        language = self.hass.config.language
        is_russian = language == "ru"
        
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return f"{base_name} {'температура' if is_russian else 'temperature'}"
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            return f"{base_name} {'время приготовления' if is_russian else 'cooking time'} {'часы' if is_russian else 'hours'}"
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            return f"{base_name} {'время приготовления' if is_russian else 'cooking time'} {'минуты' if is_russian else 'minutes'}"
        elif self.number_type == NUMBER_TYPE_DELAYED_START_HOURS:
            return f"{base_name} {'отложенный старт' if is_russian else 'delayed start'} {'часы' if is_russian else 'hours'}"
        elif self.number_type == NUMBER_TYPE_DELAYED_START_MINUTES:
            return f"{base_name} {'отложенный старт' if is_russian else 'delayed start'} {'минуты' if is_russian else 'minutes'}"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return "mdi:thermometer"
        elif self.number_type in [NUMBER_TYPE_COOKING_TIME_HOURS, NUMBER_TYPE_COOKING_TIME_MINUTES]:
            return "mdi:timer"
        elif self.number_type in [NUMBER_TYPE_DELAYED_START_HOURS, NUMBER_TYPE_DELAYED_START_MINUTES]:
            return "mdi:timer-sand"
        return None

    @property
    def available(self):
        """Return if number entity is available."""
        return self.skycooker.available

    @property
    def native_value(self):
        """Return the current value."""
        current_mode = self.skycooker.status.mode if self.skycooker.status else 0
        model_type = self.skycooker.model_code
         
        # Check if we have custom values set
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            # Return target temperature from connection if set, otherwise from MODE_DATA
            if self.skycooker.target_state:
                return self.skycooker.target_state[1]
            elif model_type and model_type in MODE_DATA and current_mode < len(MODE_DATA[model_type]):
                return MODE_DATA[model_type][current_mode][0]
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            # Return hours from target boil time if set, otherwise from MODE_DATA
            if self.skycooker.target_boil_time:
                return self.skycooker.target_boil_time // 60
            elif model_type and model_type in MODE_DATA and current_mode < len(MODE_DATA[model_type]):
                return MODE_DATA[model_type][current_mode][1]
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            # Return minutes from target boil time if set, otherwise from MODE_DATA
            if self.skycooker.target_boil_time:
                return self.skycooker.target_boil_time % 60
            elif model_type and model_type in MODE_DATA and current_mode < len(MODE_DATA[model_type]):
                return MODE_DATA[model_type][current_mode][2]
        elif self.number_type == NUMBER_TYPE_DELAYED_START_HOURS:
            # For delayed start, always return from MODE_DATA if available, otherwise 0
            if model_type and model_type in MODE_DATA and current_mode < len(MODE_DATA[model_type]):
                mode_data = MODE_DATA[model_type][current_mode]
                if len(mode_data) > 3:
                    return mode_data[3]
            return 0
        elif self.number_type == NUMBER_TYPE_DELAYED_START_MINUTES:
            # For delayed start, always return from MODE_DATA if available, otherwise 0
            if model_type and model_type in MODE_DATA and current_mode < len(MODE_DATA[model_type]):
                mode_data = MODE_DATA[model_type][current_mode]
                if len(mode_data) > 4:
                    return mode_data[4]
            return 0
         
        return 0

    @property
    def native_min_value(self):
        """Return the minimum value."""
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return 35
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            return 0
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            return 0
        elif self.number_type == NUMBER_TYPE_DELAYED_START_HOURS:
            return 0
        elif self.number_type == NUMBER_TYPE_DELAYED_START_MINUTES:
            return 0
        return 0

    @property
    def native_max_value(self):
        """Return the maximum value."""
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return 100
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            return 24
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            return 59
        elif self.number_type == NUMBER_TYPE_DELAYED_START_HOURS:
            return 12
        elif self.number_type == NUMBER_TYPE_DELAYED_START_MINUTES:
            return 59
        return 100

    @property
    def native_step(self):
        """Return the step size."""
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return 1
        elif self.number_type in [NUMBER_TYPE_COOKING_TIME_HOURS, NUMBER_TYPE_COOKING_TIME_MINUTES]:
            return 1
        return 1

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            return UnitOfTime.HOURS
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            return UnitOfTime.MINUTES
        return None

    @property
    def mode(self):
        """Return the mode of the number entity."""
        return "auto"

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            # Set temperature in target state
            current_mode = self.skycooker.status.mode if self.skycooker.status else 0
            self.skycooker.target_state = (current_mode, int(value))
            self.skycooker.target_temperature = int(value)
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            # Update hours in target boil time
            current_minutes = self.skycooker.target_boil_time % 60 if self.skycooker.target_boil_time else 0
            self.skycooker.target_boil_time = int(value) * 60 + current_minutes
            self.skycooker.target_cooking_time = self.skycooker.target_boil_time
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            # Update minutes in target boil time
            current_hours = self.skycooker.target_boil_time // 60 if self.skycooker.target_boil_time else 0
            self.skycooker.target_boil_time = current_hours * 60 + int(value)
            self.skycooker.target_cooking_time = self.skycooker.target_boil_time
        elif self.number_type in [NUMBER_TYPE_DELAYED_START_HOURS, NUMBER_TYPE_DELAYED_START_MINUTES]:
            # For delayed start, we can't change it directly - it's defined in MODE_DATA
            # So we just update the display
            pass
         
        # Schedule an update to refresh the entity state
        self.async_schedule_update_ha_state(True)
         
        # Log the new values for debugging
        _LOGGER.debug(f"Updated {self.number_type}: {value}")
        _LOGGER.debug(f"Current target_state: {self.skycooker.target_state}")
        _LOGGER.debug(f"Current target_boil_time: {self.skycooker.target_boil_time}")
        