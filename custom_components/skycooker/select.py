"""SkyCooker select entities."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker select entities."""
    async_add_entities([
        SkyCookerSelect(hass, entry, SELECT_TYPE_MODE),
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
        
        if self.select_type == SELECT_TYPE_MODE:
            return f"{base_name} режим"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.select_type == SELECT_TYPE_MODE:
            return "mdi:chef-hat"
        return None

    @property
    def available(self):
        """Return if select entity is available."""
        return self.skycooker.available

    @property
    def current_option(self):
        """Return the current selected option."""
        if self.select_type == SELECT_TYPE_MODE:
            mode_id = self.skycooker.current_mode
            if mode_id is not None:
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
            
            # Find the mode ID by name
            mode_id = None
            for idx, value in enumerate(mode_names[1]):
                if value == option:
                    mode_id = idx
                    break
             
            if mode_id is not None:
                # Reset target_state and target_boil_time to None so that Number entities use MODE_DATA values
                self.skycooker.target_state = None
                self.skycooker.target_boil_time = None
                await self.skycooker.set_target_mode(mode_id)
                self.update()