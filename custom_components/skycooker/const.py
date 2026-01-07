# Constants for SkyCooker integration
DOMAIN = "skycooker"

MODEL_0 = 0
MODEL_1 = 1
MODEL_2 = 2
MODEL_3 = 3
MODEL_4 = 4
MODEL_5 = 5
MODEL_6 = 6
MODEL_7 = 7

# List of supported models
SUPPORTED_MODELS = {
    "RMC-M40S": {"supported": True, "type": 3},
    "RMC-M42S": {"supported": True, "type": 3},
    "RMC-M92S": {"supported": False, "type": 6},
    "RMC-M92S-A": {"supported": False, "type": 6},
    "RMC-M92S-C": {"supported": False, "type": 6},
    "RMC-M92S-E": {"supported": False, "type": 6},
    "RMC-M222S": {"supported": False, "type": 7},
    "RMC-M222S-A": {"supported": False, "type": 7},
    "RMC-M223S": {"supported": False, "type": 7},
    "RMC-M223S-E": {"supported": False, "type": 7},
    "RMC-M224S": {"supported": False, "type": 7},
    "RFS-KMC001": {"supported": False, "type": 7},
    "RMC-M225S": {"supported": False, "type": 7},
    "RMC-M225S-E": {"supported": False, "type": 7},
    "RMC-M226S": {"supported": False, "type": 7},
    "RMC-M226S-E": {"supported": False, "type": 7},
    "JK-MC501": {"supported": False, "type": 7},
    "NK-MC10": {"supported": False, "type": 7},
    "RMC-M227S": {"supported": False, "type": 7},
    "RFS-KMC004": {"supported": False, "type": 7},
    "RMC-M800S": {"supported": False, "type": 0},
    "RMC-M903S": {"supported": False, "type": 5},
    "RFS-KMC005": {"supported": False, "type": 5},
    "RMC-961S": {"supported": False, "type": 4},
    "RMC-CBD100S": {"supported": False, "type": 1},
    "RMC-CBF390S": {"supported": False, "type": 2},
}

MODELS = {
    "RMC-M40S": MODEL_3,
    "RMC-M42S": MODEL_3,
    "RMC-M92S": MODEL_6,
    "RMC-M92S-A": MODEL_6,
    "RMC-M92S-C": MODEL_6,
    "RMC-M92S-E": MODEL_6,
    "RMC-M222S": MODEL_7,
    "RMC-M222S-A": MODEL_7,
    "RMC-M223S": MODEL_7,
    "RMC-M223S-E": MODEL_7,
    "RMC-M224S": MODEL_7,
    "RFS-KMC001": MODEL_7,
    "RMC-M225S": MODEL_7,
    "RMC-M225S-E": MODEL_7,
    "RMC-M226S": MODEL_7,
    "RMC-M226S-E": MODEL_7,
    "JK-MC501": MODEL_7,
    "NK-MC10": MODEL_7,
    "RMC-M227S": MODEL_7,
    "RFS-KMC004": MODEL_7,
    "RMC-M800S": MODEL_0,
    "RMC-M903S": MODEL_5,
    "RFS-KMC005": MODEL_5,
    "RMC-961S": MODEL_4,
    "RMC-CBD100S": MODEL_1,
    "RMC-CBF390S": MODEL_2,
}

# Mode data for each model
MODE_DATA = {
    MODEL_0: [
        [0, 0, 0, 0],
        [100, 0, 30, 15], [100, 0, 35, 7], [97, 3, 0, 7], [110, 1, 0, 7],
        [180, 0, 15, 133], [100, 1, 0, 135], [100, 0, 8, 5], [95, 0, 35, 7],
        [99, 1, 0, 7], [40, 8, 0, 6], [145, 0, 45, 7], [100, 0, 40, 135],
        [100, 0, 40, 7]
    ],
    MODEL_1: [
        [0, 0, 0, 0],
        [100, 0, 30, 15], [100, 0, 30, 7], [100, 1, 0, 135], [100, 1, 30, 7],
        [100, 0, 35, 135], [100, 0, 40, 135], [100, 0, 50, 135], [97, 3, 0, 7],
        [170, 0, 18, 133], [145, 1, 0, 7], [150, 0, 30, 7], [110, 0, 35, 7],
        [38, 8, 0, 6], [150, 3, 0, 7], [100, 0, 8, 4], [98, 0, 15, 7],
        [40, 0, 10, 7], [63, 2, 30, 6], [160, 0, 18, 132], [98, 0, 20, 7],
        [100, 0, 20, 64]
    ],
    MODEL_2: [
        [0, 0, 0, 0],
        [100, 3, 0, 135], [170, 0, 18, 133], [100, 0, 8, 4], [145, 1, 0, 7],
        [100, 1, 0, 135], [38, 8, 0, 6], [100, 0, 30, 15], [40, 0, 10, 7],
        [110, 0, 35, 7], [100, 0, 40, 135], [140, 1, 0, 7], [98, 0, 20, 7],
        [150, 3, 0, 7], [100, 0, 20, 135], [100, 0, 15, 7], [98, 0, 30, 7],
        [97, 3, 0, 7], [100, 0, 30, 4], [160, 0, 16, 132], [100, 0, 40, 135],
        [100, 0, 30, 64], [70, 0, 0, 64]
    ],
    MODEL_3: [
        [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
        [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
        [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
        [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
        [0, 0, 0, 0], [62, 2, 30, 6]
    ],
    MODEL_4: [
        [0, 0, 0, 0],
        [100, 0, 10, 7], [150, 0, 15, 5], [100, 0, 25, 7], [140, 1, 0, 7],
        [100, 1, 0, 7], [100, 0, 30, 15], [110, 1, 0, 7], [100, 1, 0, 7],
        [100, 0, 30, 7], [38, 8, 0, 6], [100, 0, 0, 64]
    ],
    MODEL_5: [
        [0, 0, 0, 0],
        [100, 0, 30, 15], [97, 0, 10, 7], [100, 1, 0, 7], [170, 0, 15, 5],
        [99, 1, 0, 7], [100, 0, 20, 7], [100, 0, 8, 4], [97, 5, 0, 7],
        [100, 0, 40, 7], [145, 1, 0, 7], [100, 0, 35, 7], [110, 1, 0, 7],
        [38, 8, 0, 6], [150, 0, 25, 7], [150, 3, 0, 7], [98, 0, 20, 7],
        [100, 0, 20, 64]
    ],
    MODEL_6: [
        [0, 0, 0, 0],
        [100, 0, 30, 15], [97, 0, 10, 7], [100, 1, 0, 7], [170, 0, 15, 5],
        [99, 1, 0, 7], [100, 0, 20, 7], [100, 0, 8, 4], [97, 5, 0, 7],
        [100, 0, 40, 7], [145, 1, 0, 7], [100, 0, 35, 7], [110, 1, 0, 7],
        [38, 8, 0, 6], [150, 0, 25, 7], [150, 3, 0, 7], [98, 0, 20, 7],
        [100, 0, 0, 64], [100, 70, 30, 64]
    ],
    MODEL_7: [
        [0, 0, 0, 0],
        [150, 0, 15, 5], [100, 0, 25, 7], [100, 0, 30, 15], [110, 1, 0, 7],
        [100, 0, 25, 7], [140, 1, 0, 7], [100, 1, 0, 7], [100, 1, 0, 7],
        [100, 0, 30, 7], [40, 8, 0, 6], [100, 0, 20, 64], [70, 0, 30, 64]
    ],
}

# Mode names for each model
MODE_NAMES = {
    MODEL_0: [
        [
            "Standby Mode",
            "Multi-chef", "Rice/Cereals", "Languor", "Pilaf",
            "Frying", "Stewing", "Pasta", "Milk porridge",
            "Soup", "Yogurt", "Baking", "Steam",
            "Cooking/Legumes"
        ],
        [
            "Режим ожидания",
            "Мультиповар", "Рис/Крупы", "Томление", "Плов",
            "Жарка", "Тушение", "Паста/Макароны", "Молочная каша",
            "Суп", "Йогурт", "Выпечка", "На пару",
            "Варка/Бобовые"
        ],
    ],
    MODEL_1: [
        [
            "Standby Mode",
            "Multi-chef", "Rice/Cereals", "Soup", "Wildfowl",
            "Steam", "Cooking", "Stewing", "Languor",
            "Frying", "Baking", "Pizza", "Pilaf",
            "Yogurt", "Bread", "Pasta", "Milk porridge",
            "Baby food", "Sous-vide", "Deep frying", "Desserts",
            "Express"
        ],
        [
            "Режим ожидания",
            "Мультиповар", "Рис/Крупы", "Суп", "Дичь",
            "Пар", "Варка", "Тушение", "Томление",
            "Жарка", "Выпечка", "Пицца", "Плов",
            "Йогурт", "Хлеб", "Паста", "Молочная каша",
            "Детское питание", "Вакуум", "Фритюр", "Десерты",
            "Экспресс"
        ],
    ],
    MODEL_2: [
        [
            "Standby Mode",
            "Galantine", "Frying", "Pasta", "Baking",
            "Stewing", "Yogurt/Dough", "Multi-chef", "Baby food",
            "Pilaf", "Soup", "Cheesecake", "Milk porridge",
            "Bread", "Steam", "Rice/Cereals", "Desserts",
            "Languor", "Sous", "Deep frying", "Cooking",
            "Express", "Warming up"
        ],
        [
            "Режим ожидания",
            "Холодец", "Жарка", "Макароны", "Выпечка",
            "Тушение", "Йогурт/Тесто", "Мультиповар", "Детское питание",
            "Плов", "Суп", "Запеканка/Чизкейк", "Молочная каша",
            "Хлеб", "На пару", "Рис/Крупы", "Десерты",
            "Томление", "Соус", "Фритюр", "Варка",
            "Экспресс", "Разогрев"
        ],
    ],
    MODEL_3: [
        [
            "Multi-chef", "Milk porridge", "Stewing", "Frying",
            "Soup", "Steam", "Pasta", "Languor",
            "Cooking", "Baking", "Rice/Cereals", "Pilaf",
            "Yogurt", "Pizza", "Bread",
            "Sous-vide", "Standby Mode"
        ],
        [
            "Мультиповар", "Молочная каша", "Тушение", "Жарка",
            "Суп", "Пар", "Паста", "Томление",
            "Варка", "Выпечка", "Рис/Крупы", "Плов",
            "Йогурт", "Пицца", "Хлеб",
            "Вакуум", "Ожидание"
        ],
    ],
    MODEL_4: [
        [
            "Standby Mode",
            "Rice/Cereals", "Frying", "Steam", "Baking",
            "Stewing", "Multi-chef", "Pilaf", "Soup",
            "Milk porridge", "Yogurt", "Express"
        ],
        [
            "Режим ожидания",
            "Рис/Крупы", "Жарка", "На пару", "Выпечка",
            "Тушение", "Мультиповар", "Плов", "Суп",
            "Молочная каша", "Йогурт", "Экспресс"
        ],
    ],
    MODEL_5: [
        [
            "Standby Mode",
            "Multi-chef", "Milk porridge", "Stewing", "Frying",
            "Soup", "Steam", "Pasta", "Languor",
            "Cooking", "Baking", "Rice/Cereals", "Pilaf",
            "Yogurt", "Pizza", "Bread", "Desserts",
            "Express"
        ],
        [
            "Режим ожидания",
            "Мультиповар", "Молочная каша", "Тушение", "Жарка",
            "Суп", "На пару", "Макароны", "Томление",
            "Варка", "Выпечка", "Крупы", "Плов",
            "Йогурт", "Пицца", "Хлеб", "Десерты",
            "Экспресс"
        ],
    ],
    MODEL_6: [
        [
            "Standby Mode",
            "Multi-chef", "Milk porridge", "Stewing", "Frying",
            "Soup", "Steam", "Pasta", "Languor",
            "Cooking", "Baking", "Rice/Cereals", "Pilaf",
            "Yogurt", "Pizza", "Bread", "Desserts",
            "Express", "Warming"
        ],
        [
            "Режим ожидания",
            "Мультиповар", "Молочная каша", "Тушение", "Жарка",
            "Суп", "На пару", "Макароны", "Томление",
            "Варка", "Выпечка", "Крупы", "Плов",
            "Йогурт", "Пицца", "Хлеб", "Десерты",
            "Экспресс", "Подогрев"
        ],
    ],
    MODEL_7: [
        [
            "Standby Mode",
            "Frying", "Rice/Cereals", "Multi-chef", "Pilaf",
            "Steam", "Baking", "Stewing", "Soup",
            "Milk porridge", "Yogurt", "Express", "Warming up"
        ],
        [
            "Режим ожидания",
            "Жарка", "Рис/Крупы", "Мультиповар", "Плов",
            "На пару", "Выпечка", "Тушение", "Суп",
            "Молочная каша", "Йогурт", "Экспресс", "Разогрев"
        ],
    ],
}

# Product data for each model
PRODUCT_DATA = {
    MODEL_0: [
        [4, 18, 12, 15, 0], [5, 40, 35, 60, 0], [11, 30, 25, 40, 0]
    ],
    MODEL_1: [
        [2, 60, 50, 40, 30], [4, 35, 30, 25, 20], [5, 40, 30, 20, 18], [6, 50, 40, 20, 18],
        [8, 18, 15, 12, 16], [18, 18, 16, 15, 13]
    ],
    MODEL_2: [
        [2, 60, 50, 40, 30], [4, 35, 30, 25, 20], [5, 40, 30, 20, 18], [6, 50, 40, 20, 18],
        [8, 18, 15, 12, 16], [18, 18, 16, 15, 13]
    ],
}

# Cooking modes
# @deprecated
MODES = MODE_NAMES[MODEL_3][1] # DEPRECATED

# Product names for each model
PRODUCT_NAMES = {
    MODEL_0: [
        [
            "No choice", "Vegetables", "Fish", "Meat", "Bird"
        ],
        [
            "Нет выбора", "Овощи", "Рыба", "Мясо", "Птица"
        ],
    ],
    MODEL_1: [
        [
            "No choice", "Vegetables", "Fish", "Meat", "Bird", "Desserts"
        ],
        [
            "Нет выбора", "Овощи", "Рыба", "Мясо", "Птица", "Десерты"
        ],
    ],
    MODEL_2: [
        [
            "No choice", "Vegetables", "Fish", "Meat", "Bird", "Desserts"
        ],
        [
            "Нет выбора", "Овощи", "Рыба", "Мясо", "Птица", "Десерты"
        ],
    ],
}

# Status codes
STATUS_OFF = 0
STATUS_COOKING = 1
STATUS_HEATING = 2
STATUS_DELAYED_START = 3
STATUS_KEEP_WARM = 4
STATUS_ERROR = 5
STATUS_READY = 6

STATUS_CODES = {
    STATUS_OFF: "Выключена",
    STATUS_COOKING: "Готовка",
    STATUS_HEATING: "Разогрев",
    STATUS_DELAYED_START: "Отложенный старт",
    STATUS_KEEP_WARM: "Подогрев",
    STATUS_ERROR: "Ошибка",
    STATUS_READY: "Готова",
}


# Config flow constants
CONF_PERSISTENT_CONNECTION = "persistent_connection"
CONF_MODEL = "model"

# Default values
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PERSISTENT_CONNECTION = True

# Data keys
DATA_CONNECTION = "connection"
DATA_CANCEL = "cancel"
DATA_WORKING = "working"
DATA_DEVICE_INFO = "device_info"

# Dispatcher
DISPATCHER_UPDATE = "update"

# BLE settings
BLE_RECV_TIMEOUT = 1.5
MAX_TRIES = 3  # Like in working version
TRIES_INTERVAL = 0.5
