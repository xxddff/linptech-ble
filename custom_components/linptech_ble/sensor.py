"""Sensor platform for Linptech BLE."""

from __future__ import annotations

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.sensor import sensor_device_info_to_entity_device_info

from .const import (
    DOMAIN,
    KEY_BATTERY,
    KEY_PRESSURE_NOT_PRESENT_DURATION,
    KEY_PRESSURE_PRESENT_DURATION,
    KEY_RSSI,
    MODEL_PS1BB,
)
from .device import LinptechBluetoothDeviceData


def sensor_update_to_bluetooth_data_update(
    data: LinptechBluetoothDeviceData,
) -> PassiveBluetoothDataUpdate:
    """Convert Linptech sensor data to bluetooth data update."""
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
            KEY_BATTERY: SensorEntityDescription(
                key=KEY_BATTERY,
                device_class=SensorDeviceClass.BATTERY,
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            KEY_PRESSURE_PRESENT_DURATION: SensorEntityDescription(
                key=KEY_PRESSURE_PRESENT_DURATION,
                device_class=SensorDeviceClass.DURATION,
                native_unit_of_measurement=UnitOfTime.SECONDS,
                state_class=SensorStateClass.MEASUREMENT,
                translation_key=KEY_PRESSURE_PRESENT_DURATION,
            ),
            KEY_PRESSURE_NOT_PRESENT_DURATION: SensorEntityDescription(
                key=KEY_PRESSURE_NOT_PRESENT_DURATION,
                device_class=SensorDeviceClass.DURATION,
                native_unit_of_measurement=UnitOfTime.SECONDS,
                state_class=SensorStateClass.MEASUREMENT,
                translation_key=KEY_PRESSURE_NOT_PRESENT_DURATION,
            ),
            KEY_RSSI: SensorEntityDescription(
                key=KEY_RSSI,
                device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                state_class=SensorStateClass.MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        },
        entity_data={
            KEY_BATTERY: data.battery if hasattr(data, "battery") else None,
            KEY_PRESSURE_PRESENT_DURATION: (
                data.pressure_present_duration
                if hasattr(data, "pressure_present_duration")
                else None
            ),
            KEY_PRESSURE_NOT_PRESENT_DURATION: (
                data.pressure_not_present_duration
                if hasattr(data, "pressure_not_present_duration")
                else None
            ),
            KEY_RSSI: data.rssi if hasattr(data, "rssi") else None,
        },
        entity_names={
            KEY_BATTERY: "Battery",
            KEY_PRESSURE_PRESENT_DURATION: "Pressure Present Duration",
            KEY_PRESSURE_NOT_PRESENT_DURATION: "Pressure Not Present Duration",
            KEY_RSSI: "Signal Strength",
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Linptech BLE sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)

    entry.async_on_unload(
        processor.async_add_entities_listener(
            LinptechBluetoothSensorEntity, async_add_entities
        )
    )

    entry.async_on_unload(coordinator.async_register_processor(processor))


class LinptechBluetoothSensorEntity(PassiveBluetoothProcessorEntity, SensorEntity):
    """Linptech BLE sensor entity."""

    @property
    def native_value(self) -> int | float | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.processor.coordinator.available and self.native_value is not None
