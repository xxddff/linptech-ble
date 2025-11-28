"""Linptech BLE device data parser."""

from __future__ import annotations

from xiaomi_ble.parser import XiaomiBluetoothDeviceData

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass

from .const import (
    KEY_BATTERY,
    KEY_PRESSURE_NOT_PRESENT_DURATION,
    KEY_PRESSURE_PRESENT_DURATION,
    KEY_PRESSURE_STATE,
    OBJECT_ID_BATTERY,
    OBJECT_ID_PRESSURE_NOT_PRESENT_DURATION,
    OBJECT_ID_PRESSURE_PRESENT_DURATION,
    OBJECT_ID_PRESSURE_STATE,
)


class LinptechBluetoothDeviceData(XiaomiBluetoothDeviceData):
    """Linptech 设备数据解析器，基于 xiaomi-ble."""

    def _process_mfr_data(self, data: bytes, mac: str) -> dict[str, any]:
        """Process manufacturer data from Linptech device."""
        result = super()._process_mfr_data(data, mac)

        # 调用父类的解密和解析逻辑后，再处理 Linptech 特定的数据对象
        # xiaomi-ble 会自动解密并解析 TLV 格式的数据对象
        # 我们需要监听特定的对象 ID 并进行处理

        return result

    def _parse_xiaomi_encrypted_data(
        self, data: bytes, device_id: int, product_id: int
    ) -> dict[str, any]:
        """Parse Xiaomi encrypted advertisement data."""
        result = super()._parse_xiaomi_encrypted_data(data, device_id, product_id)

        # 处理 Linptech PS1BB 的特定数据对象
        if hasattr(self, "_obj_data"):
            for obj_id, obj_data in self._obj_data.items():
                self._process_linptech_object(obj_id, obj_data)

        return result

    def _process_linptech_object(self, obj_id: int, data: bytes) -> None:
        """处理 Linptech 特定数据对象."""

        if obj_id == OBJECT_ID_PRESSURE_STATE:
            # 0x483C: 压力状态（布尔值）
            pressure_present = data[0] == 1
            self.update_binary_sensor(
                KEY_PRESSURE_STATE,
                pressure_present,
                device_class=BinarySensorDeviceClass.OCCUPANCY,
            )

        elif obj_id == OBJECT_ID_PRESSURE_PRESENT_DURATION:
            # 0x483D: 有压力持续时间（uint32，秒）
            if len(data) >= 4:
                duration = int.from_bytes(data[:4], byteorder="little")
                self.update_sensor(
                    KEY_PRESSURE_PRESENT_DURATION,
                    duration,
                    device_class=SensorDeviceClass.DURATION,
                    native_unit_of_measurement="s",
                )

        elif obj_id == OBJECT_ID_PRESSURE_NOT_PRESENT_DURATION:
            # 0x483E: 无压力持续时间（uint32，秒）
            if len(data) >= 4:
                duration = int.from_bytes(data[:4], byteorder="little")
                self.update_sensor(
                    KEY_PRESSURE_NOT_PRESENT_DURATION,
                    duration,
                    device_class=SensorDeviceClass.DURATION,
                    native_unit_of_measurement="s",
                )

        elif obj_id == OBJECT_ID_BATTERY:
            # 0x4C03: 电池电量（uint8，百分比）
            if len(data) >= 1:
                battery = data[0]
                self.update_sensor(
                    KEY_BATTERY,
                    battery,
                    device_class=SensorDeviceClass.BATTERY,
                    native_unit_of_measurement="%",
                )
