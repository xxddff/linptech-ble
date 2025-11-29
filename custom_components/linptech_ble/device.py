"""Linptech BLE device data parser.

This module implements a minimal Xiaomi MiBeacon v4/v5 parser and
AES-CCM decryption for the Linptech PS1BB device. The implementation
is based on the published MiBeacon protocol and inspired by the
open-source ``xiaomi-ble`` library, but all code here is an independent
reimplementation (no code is copied).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from .const import (
    KEY_BATTERY,
    KEY_PRESSURE_NOT_PRESENT_DURATION,
    KEY_PRESSURE_PRESENT_DURATION,
    KEY_PRESSURE_STATE,
    KEY_RSSI,
    LOGGER,
    OBJECT_ID_BATTERY,
    OBJECT_ID_PRESSURE_NOT_PRESENT_DURATION,
    OBJECT_ID_PRESSURE_PRESENT_DURATION,
    OBJECT_ID_PRESSURE_STATE,
    OBJECT_ID_PRESSURE_PRESENT_TIME_SET,
    OBJECT_ID_PRESSURE_NOT_PRESENT_TIME_SET,
    SUPPORTED_PRODUCT_IDS,
)
from .mibeacon import decrypt_mibeacon_v4_v5


MI_SERVICE_UUID = "0000fe95-0000-1000-8000-00805f9b34fb"

# Frame control bit masks (see public MiBeacon documentation)
FRAMECTRL_ENCRYPTED = 0x0008
FRAMECTRL_MAC_PRESENT = 0x0010
FRAMECTRL_CAPABILITY_PRESENT = 0x0020
FRAMECTRL_OBJECT_PRESENT = 0x0040


@dataclass
class LinptechUpdate:
    """Parsed data for a single Linptech PS1BB advertisement."""

    address: str
    battery: int | None = None
    pressure_state: bool | None = None
    pressure_present_duration: int | None = None
    pressure_not_present_duration: int | None = None
    pressure_present_time_set: int | None = None
    pressure_not_present_time_set: int | None = None
    rssi: int | None = None


class LinptechBluetoothDeviceData:
    """Linptech device data parser using a local MiBeacon decoder."""

    def __init__(self, bindkey: bytes | None = None) -> None:
        """Initialize the Linptech device data."""
        self._bindkey = bindkey

    def update(self, service_info: BluetoothServiceInfoBleak) -> LinptechUpdate | None:
        """Update from BLE advertisement data.

        This is called by the PassiveBluetoothProcessorCoordinator whenever
        a new BLE advertisement is received for the configured address.
        It is responsible for parsing the MiBeacon v4/v5 frame, optionally
        decrypting the payload, and extracting the Linptech specific objects.
        """

        # Service Data（服务数据 - 小米 BLE 设备通常在这里发送数据）
        service_data = getattr(service_info, "service_data", {}) or {}

        # 只处理小米 MiBeacon 服务 UUID 的数据
        raw = service_data.get(MI_SERVICE_UUID)
        if raw is None or len(raw) < 5:
            return None

        frame_ctrl = int.from_bytes(raw[0:2], "little")
        product_id = int.from_bytes(raw[2:4], "little")

        # 仅处理当前支持的 Linptech 设备（目前只有 PS1BB）。
        if product_id not in SUPPORTED_PRODUCT_IDS:
            LOGGER.debug(
                "Ignoring non-Linptech device with product ID 0x%04X (address=%s)",
                product_id,
                service_info.address,
            )
            return None

        frame_cnt = raw[4]
        payload = raw[5:]

        encrypted = bool(frame_ctrl & FRAMECTRL_ENCRYPTED)
        has_mac = bool(frame_ctrl & FRAMECTRL_MAC_PRESENT)
        has_capability = bool(frame_ctrl & FRAMECTRL_CAPABILITY_PRESENT)
        has_object = bool(frame_ctrl & FRAMECTRL_OBJECT_PRESENT)

        # 先从 payload 中剥离可选的 MAC 和 capability 字段，
        # 剩余部分才是需要解密（或直接解析）的对象区。
        header_offset = 0
        if has_mac and len(payload) >= header_offset + 6:
            inner_mac = payload[header_offset : header_offset + 6]
            header_offset += 6
        if has_capability and len(payload) >= header_offset + 1:
            capability = payload[header_offset]
            header_offset += 1

        if not has_object or len(payload) <= header_offset:
            return None

        object_segment = payload[header_offset:]

        if encrypted:
            if not self._bindkey:
                LOGGER.warning(
                    "Encrypted MiBeacon payload received but no bindkey configured; "
                    "cannot decrypt."
                )
                return None

            decrypted = decrypt_mibeacon_v4_v5(
                object_segment,
                bindkey=self._bindkey,
                address=service_info.address,
                product_id=product_id,
                frame_counter=frame_cnt,
                frame_ctrl=frame_ctrl,
            )
            if decrypted is None:
                LOGGER.warning("Failed to decrypt MiBeacon payload; ignoring packet")
                return None

            objects = decrypted
        else:
            objects = object_segment
        update = LinptechUpdate(
            address=service_info.address,
            rssi=getattr(service_info, "rssi", None),
        )
        self._parse_objects(objects, update)

        if (
            update.battery is None
            and update.pressure_state is None
            and update.pressure_present_duration is None
            and update.pressure_not_present_duration is None
            and update.pressure_present_time_set is None
            and update.pressure_not_present_time_set is None
        ):
            return None

        return update

    def _parse_objects(self, payload: bytes, update: LinptechUpdate) -> None:
        """Parse MiBeacon object list into the LinptechUpdate.

        Objects are encoded as a sequence of TLV structures:

        * 2 bytes: object id (little endian)
        * 1 byte: data length (N)
        * N bytes: object data
        """

        offset = 0
        length = len(payload)
        while offset + 3 <= length:
            obj_id = int.from_bytes(payload[offset : offset + 2], "little")
            obj_len = payload[offset + 2]
            offset += 3

            if offset + obj_len > length:
                LOGGER.debug(
                    "Object 0x%04X length %d exceeds payload (len=%d)",
                    obj_id,
                    obj_len,
                    length,
                )
                break

            obj_data = payload[offset : offset + obj_len]
            offset += obj_len

            if obj_id == OBJECT_ID_PRESSURE_STATE:
                self._obj_483C(obj_data, update)
            elif obj_id == OBJECT_ID_PRESSURE_PRESENT_DURATION:
                self._obj_483D(obj_data, update)
            elif obj_id == OBJECT_ID_PRESSURE_NOT_PRESENT_DURATION:
                self._obj_483E(obj_data, update)
            elif obj_id == OBJECT_ID_PRESSURE_PRESENT_TIME_SET:
                self._obj_483F(obj_data, update)
            elif obj_id == OBJECT_ID_PRESSURE_NOT_PRESENT_TIME_SET:
                self._obj_4840(obj_data, update)
            elif obj_id == OBJECT_ID_BATTERY:
                self._obj_4C03(obj_data, update)
            else:
                LOGGER.debug(
                    "Unhandled MiBeacon object 0x%04X (len=%d, data=%s)",
                    obj_id,
                    obj_len,
                    obj_data.hex().upper(),
                )

    def _obj_483C(self, xobj: bytes, update: LinptechUpdate) -> None:
        """Handle Linptech pressure state (0x483C)."""
        if len(xobj) >= 1:
            pressure_present = xobj[0] == 1
            update.pressure_state = pressure_present

    def _obj_483D(self, xobj: bytes, update: LinptechUpdate) -> None:
        """Handle Linptech pressure present duration (0x483D)."""
        if len(xobj) >= 4:
            duration = int.from_bytes(xobj[:4], byteorder="little")
            update.pressure_present_duration = duration

    def _obj_483E(self, xobj: bytes, update: LinptechUpdate) -> None:
        """Handle Linptech pressure not present duration (0x483E)."""
        if len(xobj) >= 4:
            duration = int.from_bytes(xobj[:4], byteorder="little")
            update.pressure_not_present_duration = duration

    def _obj_483F(self, xobj: bytes, update: LinptechUpdate) -> None:
        """Handle Linptech pressure present time set (0x483F)."""
        if len(xobj) >= 4:
            duration = int.from_bytes(xobj[:4], byteorder="little")
            update.pressure_present_time_set = duration

    def _obj_4840(self, xobj: bytes, update: LinptechUpdate) -> None:
        """Handle Linptech pressure not present time set (0x4840)."""
        if len(xobj) >= 4:
            duration = int.from_bytes(xobj[:4], byteorder="little")
            update.pressure_not_present_time_set = duration

    def _obj_4C03(self, xobj: bytes, update: LinptechUpdate) -> None:
        """Handle Linptech battery level (0x4C03)."""
        if len(xobj) >= 1:
            battery = xobj[0]
            update.battery = battery

