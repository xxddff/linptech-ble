"""Constants for linptech_ble."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "linptech_ble"

# 配置键
CONF_BINDKEY = "bindkey"

# 数据对象 ID(来自 ble_monitor issue #1367 等公开资料)
OBJECT_ID_PRESSURE_STATE = 0x483C
OBJECT_ID_PRESSURE_PRESENT_DURATION = 0x483D
OBJECT_ID_PRESSURE_NOT_PRESENT_DURATION = 0x483E
# 时间设置(配置值)
OBJECT_ID_PRESSURE_PRESENT_TIME_SET = 0x483F
OBJECT_ID_PRESSURE_NOT_PRESENT_TIME_SET = 0x4840
OBJECT_ID_BATTERY = 0x4C03

# 产品 ID(MiBeacon product id)
PRODUCT_ID_PS1BB = 0x3F4C
# 当前仅支持 PS1BB，如需扩展其他 Linptech 设备，
# 只需在这里追加新的 product_id 即可。
SUPPORTED_PRODUCT_IDS: tuple[int, ...] = (PRODUCT_ID_PS1BB,)

# 设备模型
MODEL_PS1BB = "PS1BB"

# 实体键
KEY_PRESSURE_STATE = "pressure_state"
KEY_PRESSURE_PRESENT_DURATION = "pressure_present_duration"
KEY_PRESSURE_NOT_PRESENT_DURATION = "pressure_not_present_duration"
KEY_PRESSURE_PRESENT_TIME_SET = "pressure_present_time_set"
KEY_PRESSURE_NOT_PRESENT_TIME_SET = "pressure_not_present_time_set"
KEY_BATTERY = "battery"
KEY_RSSI = "rssi"
