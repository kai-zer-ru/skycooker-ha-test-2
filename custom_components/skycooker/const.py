"""Constants for SkyCoocker component."""

DOMAIN = "skycooker"
FRIENDLY_NAME = "SkyCoocker"
MANUFACTORER = "Redmond"

# Supported models
SUPPORTED_MODELS = {
    "RMC-M40S": {
        "name": "Redmond RMC-M40S",
        "supported": True,
        "uuid_service": "6e400001-b5a3-f393-e0a9-e50e24dcca9e",
        "uuid_tx": "6e400002-b5a3-f393-e0a9-e50e24dcca9e",
        "uuid_rx": "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    }
    # Other models can be added here when supported
    # "RMC-M45S": {
    #     "name": "Redmond RMC-M45S",
    #     "supported": False,
    #     "uuid_service": "...",
    #     "uuid_tx": "...",
    #     "uuid_rx": "..."
    # }
}

# Commands
COMMAND_AUTH = 0xFF
COMMAND_SET_MODE = 0x09
COMMAND_GET_STATUS = 0x06
COMMAND_START = 0x03
COMMAND_STOP = 0x04

# Modes for RMC-M40S
MODE_MULTIPOT = 0x00
MODE_MILK_PORRIDGE = 0x01
MODE_STEW = 0x02
MODE_FRYING = 0x03
MODE_SOUP = 0x04
MODE_STEAM = 0x05
MODE_PASTA = 0x06
MODE_SIMMER = 0x07
MODE_BOILING = 0x08
MODE_BAKING = 0x09
MODE_RICE_GRAINS = 0x0A
MODE_PILAF = 0x0B
MODE_YOGURT = 0x0C
MODE_PIZZA = 0x0D
MODE_BREAD = 0x0E
MODE_WAIT = 0x10
MODE_VACUUM = 0x11

# Status codes
STATUS_OFF = 0x00
STATUS_WAIT = 0x01
STATUS_DELAYED_LAUNCH = 0x02
STATUS_WARMING = 0x03
STATUS_COOKING = 0x05
STATUS_AUTO_WARM = 0x06
STATUS_FULL_OFF = 0x0A

STATUS_CODES = {
    STATUS_OFF: "Выключена",
    STATUS_WAIT: "Ожидание",
    STATUS_DELAYED_LAUNCH: "Отложенный запуск",
    STATUS_WARMING: "Разогрев",
    STATUS_COOKING: "Готовка",
    STATUS_AUTO_WARM: "Автоподогрев",
    STATUS_FULL_OFF: "Полностью выключена"
}

# Cooking modes
MODES = {
    0: "Мультиповар",
    1: "Молочная каша",
    2: "Тушение",
    3: "Жарка",
    4: "Суп",
    5: "Пар",
    6: "Паста",
    7: "Томление",
    8: "Варка",
    9: "Выпечка",
    10: "Рис/крупы",
    11: "Плов",
    12: "Йогурт",
    13: "Пицца",
    14: "Хлеб",
    16: "Ожидание",
    17: "Вакуум"
}

# Config flow constants
CONF_PERSISTENT_CONNECTION = "persistent_connection"
CONF_MODEL = "model"

# Default values
DEFAULT_SCAN_INTERVAL = 5
DEFAULT_PERSISTENT_CONNECTION = True

# Data keys
DATA_CONNECTION = "connection"
DATA_CANCEL = "cancel"
DATA_WORKING = "working"
DATA_DEVICE_INFO = "device_info"

# Dispatcher
DISPATCHER_UPDATE = "update"

# BLE settings
BLE_SCAN_TIME = 3
BLE_RECV_TIMEOUT = 1.5
MAX_TRIES = 3
TRIES_INTERVAL = 0.5
STATS_INTERVAL = 15
TARGET_TTL = 30

# Temperature constants
ROOM_TEMP = 25
BOIL_TEMP = 100