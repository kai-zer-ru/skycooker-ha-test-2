"""
Constants for SkyCooker integration.
"""

# Domain name
DOMAIN = "skycooker"

# Device types
DEVICE_TYPE_RMC_M40S = "RMC-M40S"
# DEVICE_TYPE_RMC_M90S = "RMC-M90S"  # Commented out as not supported yet

# Supported device types
SUPPORTED_DEVICES = [DEVICE_TYPE_RMC_M40S]

# Bluetooth service UUIDs (common for all devices)
SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
CHAR_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Write characteristic
CHAR_TX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Notify characteristic

# Configuration
CONF_DEVICE_TYPE = "device_type"
CONF_DEVICE_ADDRESS = "device_address"
CONF_DEVICE_NAME = "device_name"

# Device-specific constants
def get_device_constants(device_type):
    """Get constants for a specific device type."""
    if device_type == DEVICE_TYPE_RMC_M40S:
        return {
            # Commands
            "COMMAND_AUTH": 0xFF,
            "COMMAND_SET_MODE": 0x09,
            "COMMAND_GET_STATUS": 0x06,
            "COMMAND_START": 0x03,
            "COMMAND_STOP": 0x04,
            
            # Status codes
            "STATUS_OFF": 0x00,
            "STATUS_WAIT": 0x01,
            "STATUS_DELAYED_LAUNCH": 0x02,
            "STATUS_WARMING": 0x03,
            "STATUS_COOKING": 0x05,
            "STATUS_AUTO_WARM": 0x06,
            "STATUS_FULL_OFF": 0x0A,
            
            # Modes
            "MODE_MULTIPOT": 0x00,
            "MODE_MILK_PORRIDGE": 0x01,
            "MODE_STEW": 0x02,
            "MODE_FRYING": 0x03,
            "MODE_SOUP": 0x04,
            "MODE_STEAM": 0x05,
            "MODE_PASTA": 0x06,
            "MODE_SIMMER": 0x07,
            "MODE_BOILING": 0x08,
            "MODE_BAKING": 0x09,
            "MODE_RICE_GRAINS": 0x0A,
            "MODE_PILAF": 0x0B,
            "MODE_YOGURT": 0x0C,
            "MODE_PIZZA": 0x0D,
            "MODE_BREAD": 0x0E,
            "MODE_WAIT": 0x10,
            "MODE_VACUUM": 0x11,
            
            # Mode names mapping
            "MODES": {
                0x00: "Мультиповар",
                0x01: "Молочная каша",
                0x02: "Тушение",
                0x03: "Жарка",
                0x04: "Суп",
                0x05: "Пар",
                0x06: "Паста",
                0x07: "Томление",
                0x08: "Варка",
                0x09: "Выпечка",
                0x0A: "Рис/крупы",
                0x0B: "Плов",
                0x0C: "Йогурт",
                0x0D: "Пицца",
                0x0E: "Хлеб",
                0x10: "Ожидание",
                0x11: "Вакуум",
            },
            
            # Status codes mapping
            "STATUS_CODES": {
                0x00: "Выключена",
                0x01: "Ожидание",
                0x02: "Отложенный запуск",
                0x03: "Разогрев",
                0x05: "Готовка",
                0x06: "Автоподогрев",
                0x0A: "Полностью выключена",
            }
        }
    # elif device_type == DEVICE_TYPE_RMC_M90S:
    #     return {
    #         # Commands for RMC-M90S
    #         "COMMAND_AUTH": 0xFF,
    #         "COMMAND_SET_MODE": 0x10,
    #         "COMMAND_GET_STATUS": 0x11,
    #         "COMMAND_START": 0x12,
    #         "COMMAND_STOP": 0x13,
    #
    #         # Status codes for RMC-M90S
    #         "STATUS_OFF": 0x00,
    #         "STATUS_WAIT": 0x01,
    #         "STATUS_DELAYED_LAUNCH": 0x02,
    #         "STATUS_WARMING": 0x03,
    #         "STATUS_COOKING": 0x04,
    #         "STATUS_AUTO_WARM": 0x05,
    #         "STATUS_FULL_OFF": 0x06,
    #
    #         # Modes for RMC-M90S
    #         "MODE_MULTIPOT": 0x00,
    #         "MODE_MILK_PORRIDGE": 0x01,
    #         "MODE_STEW": 0x02,
    #         "MODE_FRYING": 0x03,
    #         "MODE_SOUP": 0x04,
    #         "MODE_STEAM": 0x05,
    #         "MODE_PASTA": 0x06,
    #         "MODE_SIMMER": 0x07,
    #         "MODE_BOILING": 0x08,
    #         "MODE_BAKING": 0x09,
    #         "MODE_RICE_GRAINS": 0x0A,
    #         "MODE_PILAF": 0x0B,
    #         "MODE_YOGURT": 0x0C,
    #         "MODE_PIZZA": 0x0D,
    #         "MODE_BREAD": 0x0E,
    #         "MODE_WAIT": 0x0F,
    #         "MODE_VACUUM": 0x10,
    #
    #         # Mode names mapping
    #         "MODES": {
    #             0x00: "Мультиповар",
    #             0x01: "Молочная каша",
    #             0x02: "Тушение",
    #             0x03: "Жарка",
    #             0x04: "Суп",
    #             0x05: "Пар",
    #             0x06: "Паста",
    #             0x07: "Томление",
    #             0x08: "Варка",
    #             0x09: "Выпечка",
    #             0x0A: "Рис/крупы",
    #             0x0B: "Плов",
    #             0x0C: "Йогурт",
    #             0x0D: "Пицца",
    #             0x0E: "Хлеб",
    #             0x0F: "Ожидание",
    #             0x10: "Вакуум",
    #         },
    #
    #         # Status codes mapping
    #         "STATUS_CODES": {
    #             0x00: "Выключена",
    #             0x01: "Ожидание",
    #             0x02: "Отложенный запуск",
    #             0x03: "Разогрев",
    #             0x04: "Готовка",
    #             0x05: "Автоподогрев",
    #             0x06: "Полностью выключена",
    #         }
    #     }
    else:
        raise ValueError(f"Unsupported device type: {device_type}")