"""Binary sensor platform for Linptech BLE."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.sensor import sensor_device_info_to_entity_device_info

from .const import DOMAIN, KEY_PRESSURE_STATE, MODEL_PS1BB
from .device import LinptechBluetoothDeviceData


def binary_sensor_update_to_bluetooth_data_update(
    data: LinptechBluetoothDeviceData,
) -> PassiveBluetoothDataUpdate:
    """Convert Linptech binary sensor data to bluetooth data update."""
    return PassiveBluetoothDataUpdate(
        devices={
            data.address: sensor_device_info_to_entity_device_info(
                {
                    "name": f"Linptech {MODEL_PS1BB} {data.address[-5:]}",
                    "model": MODEL_PS1BB,
                    "manufacturer": "Linptech",
                    "sw_version": None,
                    "hw_version": None,
                }
            )
        },
        entity_descriptions={
            KEY_PRESSURE_STATE: BinarySensorEntityDescription(
                key=KEY_PRESSURE_STATE,
                device_class=BinarySensorDeviceClass.OCCUPANCY,
                translation_key=KEY_PRESSURE_STATE,
            ),
        },
        entity_data={
            KEY_PRESSURE_STATE: (
                data.pressure_state if hasattr(data, "pressure_state") else None
            ),
        },
        entity_names={
            KEY_PRESSURE_STATE: "Pressure State",
        },
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

    entry.async_on_unload(coordinator.async_register_processor(processor))


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
        """Return True if entity is available."""
        return self.processor.coordinator.available and self.is_on is not None
