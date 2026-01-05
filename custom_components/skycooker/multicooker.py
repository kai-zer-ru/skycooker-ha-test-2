"""
Multicooker device implementation for SkyCooker integration.

Реализация устройства мультиварки для интеграции SkyCooker.
"""

import asyncio
from bleak import BleakClient, BleakError
from bleak_retry_connector import establish_connection

from .logger import logger
from .const import get_device_constants, SERVICE_UUID, CHAR_RX_UUID, CHAR_TX_UUID

class SkyCookerDevice:
    """Main device class for Redmond multicooker. / Основной класс устройства для мультиварки Redmond."""
    
    def __init__(self, device_type, device_address, device_name):
        """Initialize the device. / Инициализация устройства."""
        self.device_type = device_type
        self.device_address = device_address
        self.device_name = device_name
        self.client = None
        self.rx_char = None
        self.tx_char = None
        self.constants = get_device_constants(device_type)
        self.connected = False
        self.status_data = {}
        self.command_success_rate = 100.0
        self.total_commands = 0
        self.successful_commands = 0
    
    async def connect(self):
        """Connect to the multicooker device."""
        logger.bluetooth(f"📡 Connecting to {self.device_name} ({self.device_address})...")
        
        try:
            # Establish connection with retry
            self.client = await establish_connection(
                BleakClient,
                self.device_address,
                self.device_name,
                max_attempts=3,
                timeout=10.0
            )
            
            logger.connect(f"🔌 Connected to {self.device_name}")
            self.connected = True
            
            # Discover services
            await self._discover_services()
            
            # Authenticate
            await self._authenticate()
            
            return True
            
        except BleakError as e:
            logger.error(f"❌ Failed to connect to {self.device_name}: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to {self.device_name}: {e}")
            self.connected = False
            return False
    
    async def _discover_services(self):
        """Discover BLE services and characteristics."""
        logger.device(f"📱 Discovering services for {self.device_name}...")
        
        try:
            # Get services
            services = await self.client.get_services()
            
            # Find our service
            service = None
            for s in services:
                if s.uuid == SERVICE_UUID:
                    service = s
                    break
            
            if not service:
                logger.error(f"❌ Service {SERVICE_UUID} not found")
                return False
            
            # Find characteristics
            for char in service.characteristics:
                if char.uuid == CHAR_RX_UUID:
                    self.rx_char = char
                    logger.device(f"📱 Found RX characteristic: {char.uuid}")
                elif char.uuid == CHAR_TX_UUID:
                    self.tx_char = char
                    logger.device(f"📱 Found TX characteristic: {char.uuid}")
            
            if not self.rx_char or not self.tx_char:
                logger.error("❌ Required characteristics not found")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error discovering services: {e}")
            return False
    
    async def _authenticate(self):
        """Authenticate with the device."""
        logger.auth(f"🔑 Authenticating with {self.device_name}...")
        
        try:
            # Create authentication packet
            auth_packet = self._create_packet(self.constants["COMMAND_AUTH"])
            
            # Write authentication command
            await self.client.write_gatt_char(self.rx_char.uuid, auth_packet)
            logger.command(f"📤 Sent authentication command: {auth_packet.hex()}")
            
            # Wait for response
            await asyncio.sleep(1.0)
            
            # Read response
            response = await self.client.read_gatt_char(self.tx_char.uuid)
            logger.response(f"📥 Received authentication response: {response.hex()}")
            
            # Check if authentication was successful
            if response and len(response) >= 4 and response[0] == 0x55 and response[-1] == 0xAA:
                if response[2] == self.constants["COMMAND_AUTH"] and response[3] == 0x01:
                    logger.auth("🔑 Authentication successful!")
                    return True
            
            logger.warning("⚠️ Authentication may have failed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def _create_packet(self, command, data=None, iteration=0):
        """Create R4S protocol packet."""
        packet = bytearray()
        packet.append(0x55)  # Start byte
        packet.append(iteration & 0xFF)  # Iteration counter
        packet.append(command & 0xFF)  # Command
        
        if data:
            packet.extend(data)
        
        packet.append(0xAA)  # End byte
        return bytes(packet)
    
    async def get_status(self):
        """Get current status from the multicooker."""
        logger.status(f"📊 Requesting status from {self.device_name}...")
        
        if not self.connected:
            logger.error("❌ Device not connected")
            return None
        
        try:
            # Create status request packet
            status_packet = self._create_packet(self.constants["COMMAND_GET_STATUS"])
            
            # Send command
            await self.client.write_gatt_char(self.rx_char.uuid, status_packet)
            logger.command(f"📤 Sent status request: {status_packet.hex()}")
            self.total_commands += 1
            
            # Wait for response
            await asyncio.sleep(1.0)
            
            # Read response
            response = await self.client.read_gatt_char(self.tx_char.uuid)
            logger.response(f"📥 Received status response: {response.hex()}")
            
            # Parse response
            status_data = self._parse_status_response(response)
            if status_data:
                self.successful_commands += 1
                self.status_data = status_data
                self._update_success_rate()
                return status_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting status: {e}")
            self._update_success_rate()
            return None
    
    def _parse_status_response(self, response):
        """Parse status response from device."""
        if not response or len(response) < 15:
            logger.warning(f"⚠️ Invalid status response length: {len(response)}")
            return None
        
        # Check packet format
        if response[0] != 0x55 or response[-1] != 0xAA:
            logger.warning(f"⚠️ Invalid packet format: {response.hex()}")
            return None
        
        # Extract data
        mode = response[3]
        status = response[11]
        temperature = response[5]
        hours = response[6]
        minutes = response[7]
        remaining_hours = response[8]
        remaining_minutes = response[9]
        auto_warm = response[10]
        
        return {
            "mode": mode,
            "mode_name": self.constants["MODES"].get(mode, f"Unknown ({mode})"),
            "status": status,
            "status_text": self.constants["STATUS_CODES"].get(status, f"Unknown ({status})"),
            "temperature": temperature,
            "time_hours": hours,
            "time_minutes": minutes,
            "time_total": hours * 60 + minutes,
            "remaining_hours": remaining_hours,
            "remaining_minutes": remaining_minutes,
            "remaining_time_total": remaining_hours * 60 + remaining_minutes,
            "auto_warm_enable": bool(auto_warm)
        }
    
    async def set_mode(self, mode):
        """Set cooking mode."""
        logger.command(f"🍲 Setting mode to {mode} ({self.constants['MODES'].get(mode, 'Unknown')})")
        
        if not self.connected:
            logger.error("❌ Device not connected")
            return False
        
        try:
            # Create mode set packet
            mode_packet = self._create_packet(self.constants["COMMAND_SET_MODE"], bytes([mode]))
            
            # Send command
            await self.client.write_gatt_char(self.rx_char.uuid, mode_packet)
            logger.command(f"📤 Sent mode set command: {mode_packet.hex()}")
            self.total_commands += 1
            
            # Wait for response
            await asyncio.sleep(1.0)
            
            # Read response
            response = await self.client.read_gatt_char(self.tx_char.uuid)
            logger.response(f"📥 Received mode set response: {response.hex()}")
            
            # Check if successful
            if response and len(response) >= 4 and response[3] == 0x01:
                self.successful_commands += 1
                self._update_success_rate()
                return True
            
            logger.warning("⚠️ Mode set may have failed")
            self._update_success_rate()
            return False
            
        except Exception as e:
            logger.error(f"❌ Error setting mode: {e}")
            self._update_success_rate()
            return False
    
    async def start(self):
        """Start cooking program."""
        logger.command(f"🚀 Starting cooking program on {self.device_name}")
        
        if not self.connected:
            logger.error("❌ Device not connected")
            return False
        
        try:
            # Create start packet
            start_packet = self._create_packet(self.constants["COMMAND_START"])
            
            # Send command
            await self.client.write_gatt_char(self.rx_char.uuid, start_packet)
            logger.command(f"📤 Sent start command: {start_packet.hex()}")
            self.total_commands += 1
            
            # For start command, there might be no response or it might be different
            # So we consider it successful if no exception was raised
            self.successful_commands += 1
            self._update_success_rate()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting program: {e}")
            self._update_success_rate()
            return False
    
    async def stop(self):
        """Stop cooking program."""
        logger.command(f"🛑 Stopping cooking program on {self.device_name}")
        
        if not self.connected:
            logger.error("❌ Device not connected")
            return False
        
        try:
            # Create stop packet
            stop_packet = self._create_packet(self.constants["COMMAND_STOP"])
            
            # Send command
            await self.client.write_gatt_char(self.rx_char.uuid, stop_packet)
            logger.command(f"📤 Sent stop command: {stop_packet.hex()}")
            self.total_commands += 1
            
            # Wait for response
            await asyncio.sleep(1.0)
            
            # Read response
            response = await self.client.read_gatt_char(self.tx_char.uuid)
            logger.response(f"📥 Received stop response: {response.hex()}")
            
            # Check if successful
            if response and len(response) >= 4 and response[3] == 0x01:
                self.successful_commands += 1
                self._update_success_rate()
                return True
            
            logger.warning("⚠️ Stop command may have failed")
            self._update_success_rate()
            return False
            
        except Exception as e:
            logger.error(f"❌ Error stopping program: {e}")
            self._update_success_rate()
            return False
    
    def _update_success_rate(self):
        """Update command success rate."""
        if self.total_commands > 0:
            self.command_success_rate = (self.successful_commands / self.total_commands) * 100.0
            logger.status(f"📊 Command success rate: {self.command_success_rate:.1f}%")
    
    async def disconnect(self):
        """Disconnect from the device."""
        logger.disconnect(f"🔌 Disconnecting from {self.device_name}...")
        
        try:
            if self.client and self.connected:
                await self.client.disconnect()
                self.connected = False
                logger.disconnect(f"🔌 Disconnected from {self.device_name}")
        except Exception as e:
            logger.error(f"❌ Error disconnecting: {e}")
        finally:
            self.client = None
            self.rx_char = None
            self.tx_char = None