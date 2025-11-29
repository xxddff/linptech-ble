"""Sensor platform for Linptech BLE."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    KEY_BATTERY,
    KEY_PRESSURE_NOT_PRESENT_DURATION,
    KEY_PRESSURE_NOT_PRESENT_TIME_SET,
    KEY_PRESSURE_PRESENT_DURATION,
    KEY_PRESSURE_PRESENT_TIME_SET,
    KEY_RSSI,
    MODEL_PS1BB,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .device import LinptechUpdate


def sensor_update_to_bluetooth_data_update(
    update: LinptechUpdate | None,
) -> PassiveBluetoothDataUpdate:
    """
    Convert a LinptechUpdate to a bluetooth data update.

    The PassiveBluetoothProcessorCoordinator passes the LinptechUpdate
    object returned by LinptechBluetoothDeviceData.update. We map that
    into Home Assistant's PassiveBluetoothDataUpdate structure.
    """
    if update is None:
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

    entity_descriptions: dict[PassiveBluetoothEntityKey, SensorEntityDescription] = {}
    entity_data: dict[PassiveBluetoothEntityKey, int | float | None] = {}
    entity_names: dict[PassiveBluetoothEntityKey, str] = {}

    # 电量
    if update.battery is not None:
        entity_key = PassiveBluetoothEntityKey(KEY_BATTERY, device_id)
        entity_descriptions.setdefault(
            entity_key,
            SensorEntityDescription(
                key=KEY_BATTERY,
                device_class=SensorDeviceClass.BATTERY,
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )
        entity_data[entity_key] = update.battery
        entity_names.setdefault(entity_key, "Battery")

    # 压力存在时长
    if update.pressure_present_duration is not None:
        entity_key = PassiveBluetoothEntityKey(KEY_PRESSURE_PRESENT_DURATION, device_id)
        entity_descriptions.setdefault(
            entity_key,
            SensorEntityDescription(
                key=KEY_PRESSURE_PRESENT_DURATION,
                device_class=SensorDeviceClass.DURATION,
                native_unit_of_measurement=UnitOfTime.SECONDS,
                state_class=SensorStateClass.MEASUREMENT,
                translation_key=KEY_PRESSURE_PRESENT_DURATION,
            ),
        )
        entity_data[entity_key] = update.pressure_present_duration
        entity_names.setdefault(entity_key, "Pressure Present Duration")

    # 压力不存在时长
    if update.pressure_not_present_duration is not None:
        entity_key = PassiveBluetoothEntityKey(
            KEY_PRESSURE_NOT_PRESENT_DURATION, device_id
        )
        entity_descriptions.setdefault(
            entity_key,
            SensorEntityDescription(
                key=KEY_PRESSURE_NOT_PRESENT_DURATION,
                device_class=SensorDeviceClass.DURATION,
                native_unit_of_measurement=UnitOfTime.SECONDS,
                state_class=SensorStateClass.MEASUREMENT,
                translation_key=KEY_PRESSURE_NOT_PRESENT_DURATION,
            ),
        )
        entity_data[entity_key] = update.pressure_not_present_duration
        entity_names.setdefault(entity_key, "Pressure Not Present Duration")

    # 压力存在时间设置(配置值)
    if update.pressure_present_time_set is not None:
        entity_key = PassiveBluetoothEntityKey(KEY_PRESSURE_PRESENT_TIME_SET, device_id)
        entity_descriptions.setdefault(
            entity_key,
            SensorEntityDescription(
                key=KEY_PRESSURE_PRESENT_TIME_SET,
                device_class=SensorDeviceClass.DURATION,
                native_unit_of_measurement=UnitOfTime.SECONDS,
                state_class=SensorStateClass.MEASUREMENT,
                translation_key=KEY_PRESSURE_PRESENT_TIME_SET,
            ),
        )
        entity_data[entity_key] = update.pressure_present_time_set
        entity_names.setdefault(entity_key, "Pressure Present Time Set")

    # 压力不存在时间设置(配置值)
    if update.pressure_not_present_time_set is not None:
        entity_key = PassiveBluetoothEntityKey(
            KEY_PRESSURE_NOT_PRESENT_TIME_SET, device_id
        )
        entity_descriptions.setdefault(
            entity_key,
            SensorEntityDescription(
                key=KEY_PRESSURE_NOT_PRESENT_TIME_SET,
                device_class=SensorDeviceClass.DURATION,
                native_unit_of_measurement=UnitOfTime.SECONDS,
                state_class=SensorStateClass.MEASUREMENT,
                translation_key=KEY_PRESSURE_NOT_PRESENT_TIME_SET,
            ),
        )
        entity_data[entity_key] = update.pressure_not_present_time_set
        entity_names.setdefault(entity_key, "Pressure Not Present Time Set")

    # RSSI 诊断传感器
    if update.rssi is not None:
        entity_key = PassiveBluetoothEntityKey(KEY_RSSI, device_id)
        entity_descriptions.setdefault(
            entity_key,
            SensorEntityDescription(
                key=KEY_RSSI,
                device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                state_class=SensorStateClass.MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        )
        entity_data[entity_key] = update.rssi
        entity_names.setdefault(entity_key, "BLE RSSI")

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
    """Set up Linptech BLE sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)

    entry.async_on_unload(
        processor.async_add_entities_listener(
            LinptechBluetoothSensorEntity, async_add_entities
        )
    )

    entry.async_on_unload(
        coordinator.async_register_processor(processor, SensorEntityDescription)
    )


class LinptechBluetoothSensorEntity(PassiveBluetoothProcessorEntity, SensorEntity):
    """Linptech BLE sensor entity."""

    @property
    def native_value(self) -> int | float | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)
