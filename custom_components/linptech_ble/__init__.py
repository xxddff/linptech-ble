"""
Custom integration to integrate Linptech BLE with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/linptech_ble
"""

from __future__ import annotations

from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_BINDKEY, DOMAIN, LOGGER
from .device import LinptechBluetoothDeviceData

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Linptech BLE from a config entry."""
    address = entry.data[CONF_ADDRESS]
    bindkey_str = entry.data[CONF_BINDKEY]

    # 将 bindkey 从十六进制字符串转换为 bytes
    try:
        bindkey = bytes.fromhex(bindkey_str)
    except ValueError:
        LOGGER.error("Invalid bindkey format for device %s", address)
        return False

    LOGGER.debug(
        "Setting up Linptech BLE device %s with bindkey",
        address,
    )

    # 创建设备数据处理器
    device_data = LinptechBluetoothDeviceData(bindkey=bindkey)

    # 创建被动蓝牙协调器
    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=device_data.update,
    )

    # 保存协调器到 hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # 转发到平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 添加重新加载监听器
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
