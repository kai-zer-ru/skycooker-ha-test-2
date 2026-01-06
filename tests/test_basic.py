"""Basic tests for SkyCoocker integration."""
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
        self.assertEqual(len(STATUS_CODES), 7)
        self.assertEqual(STATUS_CODES[STATUS_OFF], "Выключена")
        self.assertEqual(STATUS_CODES[STATUS_COOKING], "Готовка")


class TestMulticookerConnection(unittest.TestCase):
    """Test multicooker connection."""
    
    @patch('custom_components.skycooker.multicooker_connection.BleakClientWithServiceCache')
    @patch('custom_components.skycooker.multicooker_connection.bluetooth.async_ble_device_from_address')
    def test_initialization(self, mock_device_from_address, mock_bleak_client):
        """Test connection initialization."""
        from custom_components.skycooker.multicooker_connection import MulticookerConnection
        
        # Mock device and client
        mock_device = MagicMock()
        mock_device_from_address.return_value = mock_device
        
        mock_client = MagicMock()
        mock_client.is_connected = False
        mock_bleak_client.return_value = mock_client
        
        # Create connection
        connection = MulticookerConnection(
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


if __name__ == '__main__':
    unittest.main()