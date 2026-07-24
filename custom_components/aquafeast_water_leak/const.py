"""Constants for Aquafeast Water Leak integration."""

DOMAIN = "aquafeast_water_leak"
DEFAULT_NAME = "Aquafeast Water Leak"

CONF_MAC = "mac_address"
CONF_DEVICE_TYPE = "device_type"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 30

DEVICE_TYPE_LEAKAGE_PROTECTOR = "leakage_protector"
DEVICE_TYPE_FILTER = "leakage_protector_pre_filter"

API_DEVICE_MODEL = "BSK_BR"

CAP_FILTER = "filter_features"

BASE_URL = "https://interface.briskworld.com"
GET_STATE_URL = f"{BASE_URL}/devSta/getState/app"
CONTROL_URL = f"{BASE_URL}/device/control/app"
SET_MODE_URL = f"{BASE_URL}/device/setMode/app"
SET_HOUR_URL = f"{BASE_URL}/device/setHour/app"

MANUFACTURER = "Aquafeast"
MODEL = "Water Leak Controller"

KEY_DATA = "data"
KEY_STATE = "state"

KEY_VALVE = "data01"
KEY_MODE = "data02"
KEY_TEMPERATURE = "data04"
KEY_NETWORK_METHOD = "data05"
KEY_UNIT_SYSTEM = "data09"
KEY_FLOW = "data0B"

KEY_MODE4_HOURS = "data0D"
KEY_MODE5_HOURS = "data0E"
KEY_MODE6_HOURS = "data0F"

KEY_TOTAL_WATER_LOW = "data10"
KEY_TOTAL_WATER_HIGH = "data11"

KEY_PREVIOUS_MODE = "data16"
KEY_FLUSH_PERIOD = "data17"
KEY_FLUSH_DURATION = "data18"
KEY_NEXT_FLUSH_HOURS = "data19"
KEY_FLUSH_STATUS = "data1B"

KEY_BATTERY_LEVEL = "data1C"
KEY_POWER_STATUS = "data1D"

KEY_MODE4_WARNING_FLOW = "data1F"
KEY_MODE5_WARNING_FLOW = "data20"
KEY_MODE6_WARNING_FLOW = "data21"
KEY_WARNING_MIN_FLOW = "data22"

KEY_FAULT = "dataF0"
