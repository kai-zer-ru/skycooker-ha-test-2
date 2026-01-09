"""Basic tests for SkyCooker integration."""
import unittest
from unittest.mock import MagicMock, patch

from custom_components.skycooker.const import *


class TestConstants(unittest.TestCase):
    """Test constants."""
    
    def test_domain(self):
        """Test domain constant."""
        self.assertEqual(DOMAIN, "skycooker")
    
    def test_supported_models(self):
        """Test supported models."""
        self.assertIn("RMC-M40S", SUPPORTED_MODELS)
        self.assertTrue(SUPPORTED_MODELS["RMC-M40S"]["supported"])
    
    def test_modes(self):
        """Test cooking modes."""
        self.assertEqual(len(MODES), 17)  # 16 modes + 1 unknown
        self.assertEqual(MODES[0], "Мультиповар")
        self.assertEqual(MODES[16], "Ожидание")
    
    def test_status_codes(self):
        """Test status codes."""
        # STATUS_CODES is now a list of dictionaries for different languages
        self.assertEqual(len(STATUS_CODES), 2)  # English and Russian
        self.assertEqual(len(STATUS_CODES[0]), 5)  # English status codes
        self.assertEqual(len(STATUS_CODES[1]), 5)  # Russian status codes
        self.assertEqual(STATUS_CODES[0][STATUS_OFF], "Off")
        self.assertEqual(STATUS_CODES[1][STATUS_OFF], "Выключена")
        self.assertEqual(STATUS_CODES[0][STATUS_COOKING], "Cooking")
        self.assertEqual(STATUS_CODES[1][STATUS_COOKING], "Готовка")


class TestMulticookerConnection(unittest.TestCase):
    """Test multicooker connection."""

    @patch('custom_components.skycooker.skycooker_connection.BleakClientWithServiceCache')
    @patch('custom_components.skycooker.skycooker_connection.bluetooth.async_ble_device_from_address')
    def test_initialization(self, mock_device_from_address, mock_bleak_client):
        """Test connection initialization."""
        from custom_components.skycooker.skycooker_connection import SkyCookerConnection
        
        # Mock device and client
        mock_device = MagicMock()
        mock_device_from_address.return_value = mock_device
        
        mock_client = MagicMock()
        mock_client.is_connected = False
        mock_bleak_client.return_value = mock_client
        
        # Create connection
        connection = SkyCookerConnection(
            mac="AA:BB:CC:DD:EE:FF",
            key=[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
            persistent=True,
            adapter=None,
            hass=MagicMock(),
            model="RMC-M40S"
        )
        
        # Test properties
        self.assertEqual(connection._mac, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(connection.model, "RMC-M40S")
        self.assertFalse(connection._disposed)

    @patch('custom_components.skycooker.skycooker.SkyCooker.get_status')
    def test_status_properties(self, mock_get_status):
        """Test status properties."""
        from custom_components.skycooker.skycooker_connection import SkyCookerConnection
        from custom_components.skycooker.skycooker import SkyCooker
        
        # Create a mock status
        mock_status = SkyCooker.Status(
            mode=1,
            subprog=0,
            target_temp=100,
            target_boil_hours=0,
            target_boil_minutes=0,
            target_delayed_start_hours=0,
            target_delayed_start_minutes=30,
            auto_warm=0,
            is_on=True,
            sound_enabled=True,
            parental_control=False,
            error_code=0,
        )
        
        # Mock get_status to return our mock status
        mock_get_status.return_value = mock_status
        
        # Create connection
        connection = SkyCookerConnection(
            mac="AA:BB:CC:DD:EE:FF",
            key=[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
            persistent=True,
            adapter=None,
            hass=MagicMock(),
            model="RMC-M40S"
        )
        
        # Set the status directly
        connection._status = mock_status
        
        # Test new properties
        self.assertEqual(connection.status_code, 1)
        self.assertEqual(connection.remaining_time, 30)
        self.assertEqual(connection.total_time, 0)
        self.assertEqual(connection.delayed_start_time, 0)
        self.assertEqual(connection.auto_warm_time, 0)
        self.assertEqual(connection.auto_warm_enabled, False)

if __name__ == '__main__':
    unittest.main()