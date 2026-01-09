"""SkyCooker select entities."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker select entities."""
    async_add_entities([
        SkyCookerSelect(hass, entry, SELECT_TYPE_MODE),
        SkyCookerSelect(hass, entry, SELECT_TYPE_TEMPERATURE),
        SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_HOURS),
        SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_MINUTES),
        SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_HOURS),
        SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_MINUTES),
    ])


class SkyCookerSelect(SelectEntity):
    """Representation of a SkyCooker select entity."""

    def __init__(self, hass, entry, select_type):
        """Initialize the select entity."""
        self.hass = hass
        self.entry = entry
        self.select_type = select_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the select entity."""
        self.schedule_update_ha_state()

    @property
    def skycooker(self):
        """Get the skycooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.select_type}"

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
        """Return the name of the select entity."""
        base_name = (SKYCOOKER_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()
        
        # Determine the language index (0 for English, 1 for Russian)
        language = self.hass.config.language
        is_russian = language == "ru"
        
        if self.select_type == SELECT_TYPE_MODE:
            return f"{base_name} {'режим' if is_russian else 'mode'}"
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            return f"{base_name} {'температура' if is_russian else 'temperature'}"
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            return f"{base_name} {'время приготовления' if is_russian else 'cooking time'} {'(часы)' if is_russian else '(hours)'}"
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            return f"{base_name} {'время приготовления' if is_russian else 'cooking time'} {'(минуты)' if is_russian else '(minutes)'}"
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            return f"{base_name} {'отложенный старт' if is_russian else 'delayed start'} {'(часы)' if is_russian else '(hours)'}"
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            return f"{base_name} {'отложенный старт' if is_russian else 'delayed start'} {'(минуты)' if is_russian else '(minutes)'}"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.select_type == SELECT_TYPE_MODE:
            return "mdi:chef-hat"
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            return "mdi:thermometer"
        elif self.select_type in [SELECT_TYPE_COOKING_TIME_HOURS, SELECT_TYPE_COOKING_TIME_MINUTES]:
            return "mdi:timer"
        elif self.select_type in [SELECT_TYPE_DELAYED_START_HOURS, SELECT_TYPE_DELAYED_START_MINUTES]:
            return "mdi:timer-sand"
        return None

    @property
    def available(self):
        """Return if select entity is available."""
        return self.skycooker.available

    @property
    def current_option(self):
        """Return the current selected option."""
        if self.select_type == SELECT_TYPE_MODE:
            # Используем целевой режим, установленный пользователем, а не текущий режим устройства
            if self.skycooker.target_state and self.skycooker.target_state[0] is not None:
                mode_id = self.skycooker.target_state[0]
            else:
                # Если целевой режим не установлен, используем текущий режим устройства
                mode_id = self.skycooker.current_mode
                if mode_id is None:
                    return None
            
            # Get the model type from the connection
            model_type = self.skycooker.model_code
            if model_type is None:
                return f"Unknown ({mode_id})"
            
            # Get the mode names for the current model
            mode_names = MODE_NAMES.get(model_type, [None, None])
            if not mode_names or len(mode_names) < 2:
                return f"Unknown ({mode_id})"
            
            # Determine the language index (0 for English, 1 for Russian)
            language = self.hass.config.language
            lang_index = 0 if language == "en" else 1
            
            if mode_id < len(mode_names[lang_index]):
                return mode_names[lang_index][mode_id]
            return f"Unknown ({mode_id})"
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            # Return current temperature from connection if set, otherwise from MODE_DATA
            if self.skycooker.target_state:
                return str(self.skycooker.target_state[1])
            else:
                # Используем целевой режим, установленный пользователем, а не текущий режим устройства
                if self.skycooker.target_state and self.skycooker.target_state[0] is not None:
                    current_mode = self.skycooker.target_state[0]
                else:
                    current_mode = self.skycooker.current_mode if self.skycooker.current_mode is not None else 0
                model_type = self.skycooker.model_code
                if model_type and model_type in MODE_DATA and current_mode < len(MODE_DATA[model_type]):
                    return str(MODE_DATA[model_type][current_mode][0])
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            # Return current hours from target boil time if set, otherwise from MODE_DATA
            if self.skycooker.target_boil_time:
                return str(self.skycooker.target_boil_time // 60)
            else:
                # Используем целевой режим, установленный пользователем, а не текущий режим устройства
                if self.skycooker.target_state and self.skycooker.target_state[0] is not None:
                    current_mode = self.skycooker.target_state[0]
                else:
                    current_mode = self.skycooker.current_mode if self.skycooker.current_mode is not None else 0
                model_type = self.skycooker.model_code
                if model_type and model_type in MODE_DATA and current_mode < len(MODE_DATA[model_type]):
                    return str(MODE_DATA[model_type][current_mode][1])
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            # Return current minutes from target boil time if set, otherwise from MODE_DATA
            if self.skycooker.target_boil_time:
                return str(self.skycooker.target_boil_time % 60)
            else:
                # Используем целевой режим, установленный пользователем, а не текущий режим устройства
                if self.skycooker.target_state and self.skycooker.target_state[0] is not None:
                    current_mode = self.skycooker.target_state[0]
                else:
                    current_mode = self.skycooker.current_mode if self.skycooker.current_mode is not None else 0
                model_type = self.skycooker.model_code
                if model_type and model_type in MODE_DATA and current_mode < len(MODE_DATA[model_type]):
                    return str(MODE_DATA[model_type][current_mode][2])
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            # Return current delayed start hours from connection if set, otherwise 0
            if self.skycooker.target_delayed_start_hours is not None:
                return str(self.skycooker.target_delayed_start_hours)
            return "0"
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            # Return current delayed start minutes from connection if set, otherwise 0
            if self.skycooker.target_delayed_start_minutes is not None:
                return str(self.skycooker.target_delayed_start_minutes)
            return "0"
        return None

    @property
    def options(self):
        """Return the available options."""
        if self.select_type == SELECT_TYPE_MODE:
            # Get the model type from the connection
            model_type = self.skycooker.model_code
            if model_type is None:
                return []
            
            # Get the mode names for the current model
            mode_names = MODE_NAMES.get(model_type, [None, None])
            if not mode_names or len(mode_names) < 2:
                return []
            
            # Determine the language index (0 for English, 1 for Russian)
            language = self.hass.config.language
            lang_index = 0 if language == "en" else 1
            
            return mode_names[lang_index]
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            # Temperature options from 40 to 200 with step 5
            return [str(temp) for temp in range(40, 201, 5)]
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            # Hours options from 0 to 23
            return [str(hour) for hour in range(0, 24)]
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            # Minutes options from 0 to 59
            return [str(minute) for minute in range(0, 60)]
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            # Delayed start hours options from 0 to 23
            return [str(hour) for hour in range(0, 24)]
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            # Delayed start minutes options from 0 to 59
            return [str(minute) for minute in range(0, 60)]
        return []

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self.select_type == SELECT_TYPE_MODE:
            # Get the model type from the connection
            model_type = self.skycooker.model_code
            if model_type is None:
                return
            
            # Get the mode names for the current model
            mode_names = MODE_NAMES.get(model_type, [None, None])
            if not mode_names or len(mode_names) < 2:
                return
            
            # Determine the language index (0 for English, 1 for Russian)
            language = self.hass.config.language
            lang_index = 0 if language == "en" else 1
            
            # Find the mode ID by name
            mode_id = None
            for idx, value in enumerate(mode_names[lang_index]):
                if value == option:
                    mode_id = idx
                    break
                 
            if mode_id is not None:
                # Get MODE_DATA values for the selected mode
                model_type = self.skycooker.model_code
                if model_type and model_type in MODE_DATA and mode_id < len(MODE_DATA[model_type]):
                    mode_data = MODE_DATA[model_type][mode_id]
                    _LOGGER.info(f"Selected mode {mode_id} for model {model_type}: temperature={mode_data[0]}, hours={mode_data[1]}, minutes={mode_data[2]}")
                      
                    # Update target_state with mode data only if user hasn't set custom temperature
                    if not hasattr(self.skycooker, '_target_temperature') or self.skycooker._target_temperature is None:
                        self.skycooker.target_state = (mode_id, mode_data[0])
                      
                    # Update target_boil_time with mode data only if user hasn't set custom cooking time
                    # Check if target_boil_time is explicitly set by user (not None and not from MODE_DATA)
                    if self.skycooker.target_boil_time is None:
                        self.skycooker.target_boil_time = mode_data[1] * 60 + mode_data[2]
                        self.skycooker.target_cooking_time = self.skycooker.target_boil_time
                  
            # Call set_target_mode to send commands to the device when mode is selected
            await self.skycooker.set_target_mode(mode_id)
             
            # Ensure default values for delayed start hours and minutes only if user hasn't set them
            if self.skycooker.target_delayed_start_hours is None:
                self.skycooker.target_delayed_start_hours = 0
            if self.skycooker.target_delayed_start_minutes is None:
                self.skycooker.target_delayed_start_minutes = 0
                  
                # Trigger dispatcher update to notify Number entities about the mode change
                async_dispatcher_send(self.hass, DISPATCHER_UPDATE)
                self.update()
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            # Set temperature in target state
            current_mode = self.skycooker.target_state[0] if self.skycooker.target_state else (self.skycooker.status.mode if self.skycooker.status else 0)
            self.skycooker.target_state = (current_mode, int(option))
            # Mark that user has set custom temperature
            self.skycooker._target_temperature = int(option)
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            # Update hours in target boil time
            current_minutes = self.skycooker.target_boil_time % 60 if self.skycooker.target_boil_time else 0
            self.skycooker.target_boil_time = int(option) * 60 + current_minutes
            self.skycooker.target_cooking_time = self.skycooker.target_boil_time
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            # Update minutes in target boil time
            current_hours = self.skycooker.target_boil_time // 60 if self.skycooker.target_boil_time else 0
            self.skycooker.target_boil_time = current_hours * 60 + int(option)
            self.skycooker.target_cooking_time = self.skycooker.target_boil_time
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            # Set delayed start hours
            self.skycooker.target_delayed_start_hours = int(option)
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            # Set delayed start minutes
            self.skycooker.target_delayed_start_minutes = int(option)
         
        # Ensure default values for delayed start hours and minutes if not set
        if self.select_type == SELECT_TYPE_DELAYED_START_HOURS and self.skycooker.target_delayed_start_hours is None:
            self.skycooker.target_delayed_start_hours = 0
        if self.select_type == SELECT_TYPE_DELAYED_START_MINUTES and self.skycooker.target_delayed_start_minutes is None:
            self.skycooker.target_delayed_start_minutes = 0
         
        # Schedule an update to refresh the entity state
        self.async_schedule_update_ha_state(True)
         
        # Log the new values for debugging
        _LOGGER.debug(f"Updated {self.select_type}: {option}")
        _LOGGER.debug(f"Current target_state: {self.skycooker.target_state}")
        _LOGGER.debug(f"Current target_boil_time: {self.skycooker.target_boil_time}")
        _LOGGER.debug(f"Current target_delayed_start_hours: {self.skycooker.target_delayed_start_hours}")
        _LOGGER.debug(f"Current target_delayed_start_minutes: {self.skycooker.target_delayed_start_minutes}")