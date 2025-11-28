"""Config flow for Linptech BLE integration."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_BINDKEY, DOMAIN, LOGGER


class LinptechBleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Linptech BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_address: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to add a device manually."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # 验证 MAC 地址格式
            address = user_input[CONF_ADDRESS].upper().replace("-", ":")
            if not re.match(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$", address):
                errors["base"] = "invalid_mac_address"
            # 验证 bindkey 格式（32 位十六进制）
            elif not re.match(r"^[0-9A-Fa-f]{32}$", user_input[CONF_BINDKEY]):
                errors["base"] = "invalid_bindkey"
            else:
                # 设置 unique_id 为 MAC 地址
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                # 创建配置条目
                return self.async_create_entry(
                    title=f"Linptech PS1BB {address[-5:]}",
                    data={
                        CONF_ADDRESS: address,
                        CONF_BINDKEY: user_input[CONF_BINDKEY].lower(),
                    },
                )

        # 显示配置表单
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_ADDRESS,
                    default=(user_input or {}).get(CONF_ADDRESS, ""),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                    ),
                ),
                vol.Required(
                    CONF_BINDKEY,
                    default=(user_input or {}).get(CONF_BINDKEY, ""),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        LOGGER.debug("Discovered BLE device: %s", discovery_info.address)

        # 保存发现信息
        self._discovery_info = discovery_info
        self._discovered_address = discovery_info.address

        # 检查是否已配置
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # 进入用户确认步骤（需要输入 bindkey）
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery and get bindkey."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # 验证 bindkey 格式
            if not re.match(r"^[0-9A-Fa-f]{32}$", user_input[CONF_BINDKEY]):
                errors["base"] = "invalid_bindkey"
            else:
                # 创建配置条目
                return self.async_create_entry(
                    title=f"Linptech PS1BB {self._discovered_address[-5:]}",
                    data={
                        CONF_ADDRESS: self._discovered_address,
                        CONF_BINDKEY: user_input[CONF_BINDKEY].lower(),
                    },
                )

        # 显示 bindkey 输入表单
        data_schema = vol.Schema(
            {
                vol.Required(CONF_BINDKEY): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=data_schema,
            description_placeholders={
                "address": self._discovered_address,
            },
            errors=errors,
        )
