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
        
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return f"{base_name} температура"
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            return f"{base_name} время приготовления часы"
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            return f"{base_name} время приготовления минуты"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return "mdi:thermometer"
        elif self.number_type in [NUMBER_TYPE_COOKING_TIME_HOURS, NUMBER_TYPE_COOKING_TIME_MINUTES]:
            return "mdi:timer"
        return None

    @property
    def available(self):
        """Return if number entity is available."""
        return self.skycooker.available

    @property
    def native_value(self):
        """Return the current value."""
        if self.number_type == NUMBER_TYPE_TEMPERATURE:
            return self.skycooker.target_temperature if self.skycooker.target_temperature is not None else 0
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            # Return hours from total cooking time
            total_minutes = self.skycooker.remaining_time if self.skycooker.remaining_time is not None else 0
            return total_minutes // 60
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            # Return minutes from total cooking time
            total_minutes = self.skycooker.remaining_time if self.skycooker.remaining_time is not None else 0
            return total_minutes % 60
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
            await self.skycooker.set_temperature(int(value))
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS:
            # Get current minutes
            current_minutes = self.native_value if self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES else 0
            await self.skycooker.set_cooking_time(int(value), current_minutes)
        elif self.number_type == NUMBER_TYPE_COOKING_TIME_MINUTES:
            # Get current hours
            current_hours = self.native_value if self.number_type == NUMBER_TYPE_COOKING_TIME_HOURS else 0
            await self.skycooker.set_cooking_time(current_hours, int(value))
        
        self.update()