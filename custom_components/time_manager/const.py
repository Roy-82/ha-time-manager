"""Konstanten für den Zeitmanager."""

DOMAIN = "time_manager"
PLATFORMS = ["sensor"]

CONF_NAME = "name"
CONF_LANGUAGE = "language"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_NAME = "Zeitmanager"
DEFAULT_LANGUAGE = "auto"
DEFAULT_SCAN_INTERVAL = 30

SUPPORTED_LANGUAGES = ["auto", "de", "en"]
SUPPORTED_DOMAINS = ["switch", "light", "climate", "cover", "fan"]

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "time_manager"

SERVICE_ADD_DEVICE = "add_device"
SERVICE_UPDATE_DEVICE = "update_device"
SERVICE_REMOVE_DEVICE = "remove_device"
SERVICE_SET_DEVICE_ENABLED = "set_device_enabled"
SERVICE_ADD_SCHEDULE = "add_schedule"
SERVICE_UPDATE_SCHEDULE = "update_schedule"
SERVICE_REMOVE_SCHEDULE = "remove_schedule"
SERVICE_START_TIMER = "start_timer"
SERVICE_CANCEL_TIMER = "cancel_timer"
SERVICE_SET_ENABLED = "set_enabled"
