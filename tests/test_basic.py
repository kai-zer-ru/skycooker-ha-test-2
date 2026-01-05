"""
Basic tests for SkyCooker integration.
"""

import unittest
from custom_components.skycooker.const import get_device_constants, DEVICE_TYPE_RMC_M40S

class TestSkyCookerConstants(unittest.TestCase):
    """Test device constants."""
    
    def test_rmc_m40s_constants(self):
        """Test RMC-M40S constants."""
        constants = get_device_constants(DEVICE_TYPE_RMC_M40S)
        
        # Check that all required constants are present
        self.assertIn("COMMAND_AUTH", constants)
        self.assertIn("COMMAND_SET_MODE", constants)
        self.assertIn("COMMAND_GET_STATUS", constants)
        self.assertIn("COMMAND_START", constants)
        self.assertIn("COMMAND_STOP", constants)
        
        # Check status codes
        self.assertIn("STATUS_OFF", constants)
        self.assertIn("STATUS_WAIT", constants)
        self.assertIn("STATUS_COOKING", constants)
        
        # Check modes
        self.assertIn("MODES", constants)
        self.assertIn("MODE_MULTIPOT", constants)
        self.assertIn("MODE_SOUP", constants)
        
        # Check that MODES dictionary has expected entries
        modes = constants["MODES"]
        self.assertGreater(len(modes), 10)  # Should have at least 10 modes
        self.assertIn("Мультиповар", modes.values())
        self.assertIn("Суп", modes.values())
    
    def test_unsupported_device(self):
        """Test unsupported device type."""
        with self.assertRaises(ValueError):
            get_device_constants("UNKNOWN_DEVICE")

if __name__ == "__main__":
    unittest.main()