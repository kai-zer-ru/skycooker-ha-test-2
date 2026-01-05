"""
Button platform for SkyCooker integration.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .logger import logger
from .multicooker import SkyCookerDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SkyCooker button entities."""
    logger.info("⏯️ Setting up SkyCooker button entities")
    
    # Get device from hass data
    device = hass.data[DOMAIN][entry.entry_id]["device"]
    
    # Create button entities
    button_entities = [
        SkyCookerStartButton(device),
        SkyCookerStopButton(device),
    ]
    
    async_add_entities(button_entities)
    logger.success("✅ SkyCooker button entities setup complete")

class SkyCookerButton(ButtonEntity):
    """Base class for SkyCooker buttons."""
    
    def __init__(self, device: SkyCookerDevice, name: str, unique_suffix: str):
        """Initialize the button."""
        self._device = device
        self._attr_name = f"{device.device_name} {name}"
        self._attr_unique_id = f"{device.device_address}_{unique_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.device_address)},
            "name": device.device_name,
            "manufacturer": "Redmond",
            "model": device.device_type,
        }

class SkyCookerStartButton(SkyCookerButton):
    """Button for starting cooking program."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the start button."""
        super().__init__(device, "Start", "start_button")
    
    async def async_press(self) -> None:
        """Handle the button press."""
        logger.command(f"🚀 Start button pressed")
        success = await self._device.start()
        if success:
            logger.success("✅ Cooking program started")
        else:
            logger.error("❌ Failed to start cooking program")

class SkyCookerStopButton(SkyCookerButton):
    """Button for stopping cooking program."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the stop button."""
        super().__init__(device, "Stop", "stop_button")
    
    async def async_press(self) -> None:
        """Handle the button press."""
        logger.command(f"🛑 Stop button pressed")
        success = await self._device.stop()
        if success:
            logger.success("✅ Cooking program stopped")
        else:
            logger.error("❌ Failed to stop cooking program")