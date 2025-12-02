"""Binary sensor platform for Linptech BLE."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, KEY_PRESSURE_STATE, MODEL_PS1BB

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .device import LinptechUpdate


def binary_sensor_update_to_bluetooth_data_update(
    update: LinptechUpdate | None,
) -> PassiveBluetoothDataUpdate:
    """
    Convert a LinptechUpdate to a bluetooth data update.

    We only expose a single binary sensor: pressure_state.
    """
    if update is None or update.pressure_state is None:
        return PassiveBluetoothDataUpdate(
            devices={},
            entity_descriptions={},
            entity_data={},
            entity_names={},
        )

    address = update.address
    device_id = address.lower()

    devices: dict[str, DeviceInfo] = {
        device_id: DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"Linptech {MODEL_PS1BB} {address[-5:]}",
            model=MODEL_PS1BB,
            manufacturer="Linptech",
        )
    }

    entity_key = PassiveBluetoothEntityKey(KEY_PRESSURE_STATE, device_id)
    entity_descriptions: dict[PassiveBluetoothEntityKey, BinarySensorEntityDescription] = {
        entity_key: BinarySensorEntityDescription(
            key=KEY_PRESSURE_STATE,
            device_class=BinarySensorDeviceClass.OCCUPANCY,
            translation_key=KEY_PRESSURE_STATE,
        )
    }
    entity_data: dict[PassiveBluetoothEntityKey, bool | None] = {
        entity_key: update.pressure_state
    }
    entity_names: dict[PassiveBluetoothEntityKey, str] = {
        entity_key: "Pressure State"
    }

    return PassiveBluetoothDataUpdate(
        devices=devices,
        entity_descriptions=entity_descriptions,
        entity_data=entity_data,
        entity_names=entity_names,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Linptech BLE binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    processor = PassiveBluetoothDataProcessor(
        binary_sensor_update_to_bluetooth_data_update
    )

    entry.async_on_unload(
        processor.async_add_entities_listener(
            LinptechBluetoothBinarySensorEntity, async_add_entities
        )
    )

    entry.async_on_unload(
        coordinator.async_register_processor(
            processor, BinarySensorEntityDescription
        )
    )


class LinptechBluetoothBinarySensorEntity(
    PassiveBluetoothProcessorEntity, BinarySensorEntity
):
    """Linptech BLE binary sensor entity."""

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available.

        对于像 PS1BB 这样的 sleepy 设备，蓝牙层的“失联超时”会导致
        周期性地把设备标记为不可用，从而让实体所有属性一起变为
        unavailable。这里在协调器声明 sleepy_device 时，始终认为
        实体可用；否则使用默认逻辑。
        """
        coordinator = self.processor.coordinator
        if getattr(coordinator, "sleepy_device", False):
            return True
        return super().available
