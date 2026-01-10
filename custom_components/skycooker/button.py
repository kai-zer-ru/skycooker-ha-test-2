"""SkyCooker button entities."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import *
from .skycooker import SkyCookerError

_LOGGER = logging.getLogger(__name__)




async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker button entities."""
    async_add_entities([
        SkyCookerButton(hass, entry, BUTTON_TYPE_START),
        SkyCookerButton(hass, entry, BUTTON_TYPE_STOP),
        SkyCookerButton(hass, entry, BUTTON_TYPE_START_DELAYED),
    ])


class SkyCookerButton(ButtonEntity):
    """Representation of a SkyCooker button entity."""

    def __init__(self, hass, entry, button_type):
        """Initialize the button entity."""
        self.hass = hass
        self.entry = entry
        self.button_type = button_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the button entity."""
        self.schedule_update_ha_state()

    @property
    def skycooker(self):
        """Get the skycooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        model_name = self.entry.data.get(CONF_FRIENDLY_NAME, "")
        sanitized_model_name = sanitize_model_name(model_name)
        if self.button_type == BUTTON_TYPE_START:
            return f"button.skycooker_start_{sanitized_model_name}"
        elif self.button_type == BUTTON_TYPE_STOP:
            return f"button.skycooker_stop_{sanitized_model_name}"
        elif self.button_type == BUTTON_TYPE_START_DELAYED:
            return f"button.skycooker_start_delayed_{sanitized_model_name}"
        return f"button.skycooker_{self.button_type}_{sanitized_model_name}"

    @property
    def entity_id(self):
        """Return the entity ID."""
        return self.unique_id

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
        """Return the name of the button entity."""
        base_name = (SKYCOOKER_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()
        
        if self.button_type == BUTTON_TYPE_START:
            return f"{base_name} запуск"
        elif self.button_type == BUTTON_TYPE_STOP:
            return f"{base_name} стоп"
        elif self.button_type == BUTTON_TYPE_START_DELAYED:
            return f"{base_name} запуск с отложенным стартом"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.button_type == BUTTON_TYPE_START:
            return "mdi:play"
        elif self.button_type == BUTTON_TYPE_STOP:
            return "mdi:stop"
        elif self.button_type == BUTTON_TYPE_START_DELAYED:
            return "mdi:timer-play"
        return None

    @property
    def available(self):
        """Return if button entity is available."""
        return self.skycooker.available

    async def async_press(self) -> None:
        """Press the button."""
        try:
            if self.button_type == BUTTON_TYPE_START:
                await self.skycooker.start()
            elif self.button_type == BUTTON_TYPE_STOP:
                await self.skycooker.stop_cooking()
            elif self.button_type == BUTTON_TYPE_START_DELAYED:
                await self.skycooker.start_delayed()
        except SkyCookerError as e:
            _LOGGER.error(f"❌ Ошибка при нажатии кнопки: {str(e)}")
            # Не вызываем raise, чтобы интерфейс не падал
        except Exception as e:
            _LOGGER.error(f"❌ Неожиданная ошибка при нажатии кнопки: {str(e)}")
            # Не вызываем raise, чтобы интерфейс не падал
          
        self.update()