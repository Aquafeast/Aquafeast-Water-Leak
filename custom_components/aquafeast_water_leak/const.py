"""Constants for Aquafeast Water Leak integration."""

DOMAIN = "aquafeast_water_leak"
DEFAULT_NAME = "Aquafeast Water Leak"

CONF_MAC = "mac_address"
CONF_DEVICE_MODEL = "device_model"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_DEVICE_MODEL = "BSK_BR"
DEFAULT_SCAN_INTERVAL = 30

BASE_URL = "https://interface.briskworld.com"
GET_STATE_URL = f"{BASE_URL}/devSta/getState/app"
CONTROL_URL = f"{BASE_URL}/device/control/app"
SET_MODE_URL = f"{BASE_URL}/device/setMode/app"
SET_HOUR_URL = f"{BASE_URL}/device/setHour/app"

MANUFACTURER = "Aquafeast"
MODEL = "Water Leak Controller"
