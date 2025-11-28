"""Constants for linptech_ble."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "linptech_ble"

# 配置键
CONF_BINDKEY = "bindkey"

# 数据对象 ID（来自 ble_monitor issue #1367）
OBJECT_ID_PRESSURE_STATE = 0x483C
OBJECT_ID_PRESSURE_PRESENT_DURATION = 0x483D
OBJECT_ID_PRESSURE_NOT_PRESENT_DURATION = 0x483E
OBJECT_ID_BATTERY = 0x4C03

# 设备模型
MODEL_PS1BB = "PS1BB"

# 实体键
KEY_PRESSURE_STATE = "pressure_state"
KEY_PRESSURE_PRESENT_DURATION = "pressure_present_duration"
KEY_PRESSURE_NOT_PRESENT_DURATION = "pressure_not_present_duration"
KEY_BATTERY = "battery"
KEY_RSSI = "signal_strength"
