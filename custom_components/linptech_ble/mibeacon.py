"""MiBeacon encryption/decryption helpers for Linptech BLE.

This module contains a small, self-contained implementation of
MiBeacon v4/v5 AES-CCM decryption. It is based on the publicly
available protocol description and inspired by open-source
implementations such as the ``xiaomi-ble`` library, but the
code here is an independent reimplementation.
"""

from __future__ import annotations

from cryptography.hazmat.primitives.ciphers.aead import AESCCM

from .const import LOGGER


def decrypt_mibeacon_v4_v5(
    data: bytes,
    *,
    bindkey: bytes,
    address: str,
    product_id: int,
    frame_counter: int,
    frame_ctrl: int,
) -> bytes | None:
    """Decrypt a MiBeacon v4/v5 payload using AES-CCM.

    The algorithm follows the public description of Xiaomi's MiBeacon
    v4/v5 encryption scheme:

    * The 16-byte ``bindkey`` is used as the AES key.
    * The nonce is constructed from the reversed MAC address (little
      endian), followed by the product id and frame counter, and a
      3-byte trailer from the payload immediately before the MIC.
    * The associated data (AAD) is a fixed value of ``0x11`` for v4/v5.
    * The last 4 bytes of the payload are the MIC (authentication tag).

    The function returns the decrypted object payload on success,
    or ``None`` if decryption fails.
    """

    # We expect ``data`` to contain:
    #   <encrypted object payload> + <3-byte trailer> + <4-byte MIC>
    # and follow the same layout as MiBeacon v4/v5 frames parsed by
    # open-source implementations. The decryption parameters (nonce and
    # associated data) must match exactly, otherwise AES-CCM tag
    # verification will fail.

    # Need at least 1 byte ciphertext + 3-byte trailer + 4-byte MIC
    if len(data) < 8:
        LOGGER.debug(
            "Encrypted payload too short to contain ciphertext, trailer and MIC: len=%d",
            len(data),
        )
        return None

    try:
        mac_bytes = bytes.fromhex(address.replace(":", ""))
    except ValueError:
        LOGGER.warning("Invalid MAC address format: %s", address)
        return None

    # In MiBeacon v4/v5 the nonce is constructed as:
    #   reversed_mac + product_id(LE,2) + frame_counter(1) + data[-7:-4]
    # where data[-7:-4] are the 3 bytes immediately before the 4-byte MIC.
    header_bytes = product_id.to_bytes(2, "little") + bytes([frame_counter])
    trailer = data[-7:-4]
    nonce = mac_bytes[::-1] + header_bytes + trailer

    # Xiaomi uses a fixed associated data value of 0x11 for v4/v5.
    aad = b"\x11"

    # Ciphertext is everything before the last 7 bytes
    ciphertext = data[:-7]
    mic = data[-4:]

    try:
        aesccm = AESCCM(bindkey, tag_length=4)
    except Exception:  # pragma: no cover - cryptography import/runtime error
        LOGGER.error(
            "Failed to initialize AESCCM; cryptography library may be missing",
            exc_info=True,
        )
        return None

    try:
        # AESCCM expects ciphertext + tag concatenated
        return aesccm.decrypt(nonce, ciphertext + mic, aad)
    except Exception as err:
        LOGGER.warning("AES-CCM decryption failed for MiBeacon payload: %s", err)
        LOGGER.debug("  Nonce: %s", nonce.hex().upper())
        LOGGER.debug("  AAD: %s", aad.hex().upper())
        LOGGER.debug("  Ciphertext: %s", ciphertext.hex().upper())
        LOGGER.debug("  MIC: %s", mic.hex().upper())
        LOGGER.debug("  Trailer (for nonce): %s", trailer.hex().upper())
        return None
