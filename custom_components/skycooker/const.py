# Константы для интеграции SkyCooker

DOMAIN = "skycooker"
SIGNAL_UPDATE_DATA = 'skycooker_update'

# Тип устройства - 5 для мультиварки
DEVICE_TYPE_COOKER = 5

# Поддерживаемые устройства
SUPPORTED_DEVICES = {
    'RMC-M40S': DEVICE_TYPE_COOKER,
    'RMC-M800S': DEVICE_TYPE_COOKER,
    'RMC-M223S': DEVICE_TYPE_COOKER,
    'RMC-M92S': DEVICE_TYPE_COOKER,
    'RMC-M92S-E': DEVICE_TYPE_COOKER,
}

# Программы для мультиварки RMC-M40S
COOKER_PROGRAMS = {
    'rice': ['01', '00', '64', '00', '23', '00', '00', '01'],
    'slow_cooking': ['02', '00', '61', '03', '00', '00', '00', '01'],
    'pilaf': ['03', '00', '6e', '01', '00', '00', '00', '01'],
    'frying_vegetables': ['04', '01', 'b4', '00', '12', '00', '00', '01'],
    'frying_fish': ['04', '02', 'b4', '00', '0c', '00', '00', '01'],
    'frying_meat': ['04', '03', 'b4', '00', '0f', '00', '00', '01'],
    'stewing_vegetables': ['05', '01', '64', '00', '28', '00', '00', '01'],
    'stewing_fish': ['05', '02', '64', '00', '23', '00', '00', '01'],
    'stewing_meat': ['05', '03', '64', '01', '00', '00', '00', '01'],
    'pasta': ['06', '00', '64', '00', '08', '00', '00', '01'],
    'milk_porridge': ['07', '00', '5f', '00', '23', '00', '00', '00'],
    'soup': ['08', '00', '63', '01', '00', '00', '00', '01'],
    'yogurt': ['09', '00', '28', '08', '00', '00', '00', '00'],
    'baking': ['0a', '00', '91', '00', '2d', '00', '00', '01'],
    'steam_vegetables': ['0b', '01', '64', '00', '1e', '00', '00', '01'],
    'steam_fish': ['0b', '02', '64', '00', '19', '00', '00', '01'],
    'steam_meat': ['0b', '03', '64', '00', '28', '00', '00', '01'],
    'hot': ['0c', '00', '64', '00', '28', '00', '00', '01']
}

# Статусы
STATUS_OFF = '00'
STATUS_ON = '02'
COOKER_STATUS_PROGRAM = '01'
COOKER_STATUS_KEEP_WARM = '04'
COOKER_STATUS_DELAYED_START = '05'

# Режимы
MODE_MANUAL = '00'
MODE_AUTO = '01'

# Диапазон температур
MIN_TEMP = 35
MAX_TEMP = 200

# Диапазон времени (часы и минуты)
MIN_HOURS = 0
MAX_HOURS = 23
MIN_MINUTES = 0
MAX_MINUTES = 59

# Конфигурация
CONF_PERSISTENT_CONNECTION = "persistent_connection"
DEFAULT_PERSISTENT_CONNECTION = True
CONF_USE_BACKLIGHT = "use_backlight"