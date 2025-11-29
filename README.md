# Linptech BLE Integration for Home Assistant

A Home Assistant custom integration for Linptech BLE (Bluetooth Low Energy) devices. This integration enables local control of Linptech smart devices through Bluetooth, providing real-time monitoring without cloud dependency.

## Features

- **Local Control**: Direct Bluetooth communication with Linptech devices
- **Passive Monitoring**: Energy-efficient passive BLE scanning
- **Encrypted Communication**: Supports MiBeacon v4/v5 protocol with AES-CCM encryption
- **Real-time Updates**: Instant sensor data updates via BLE advertisements
- **Low Power**: Minimal battery impact on BLE devices

## Supported Devices

Currently supported Linptech devices:

| Model | Product ID | Description |
|-------|------------|-------------|
| PS1BB | 0x3F4C | Linptech Pressure Sensor (occupancy detection) |

## Available Entities

### Binary Sensors
- **Pressure State**: Occupancy detection (on/off)

### Sensors
- **Battery**: Battery level (%)
- **Pressure Present Duration**: Duration when pressure is detected (seconds)
- **Pressure Not Present Duration**: Duration when pressure is not detected (seconds)
- **Pressure Present Time Set**: Configured threshold for pressure present detection (seconds)
- **Pressure Not Present Time Set**: Configured threshold for pressure not present detection (seconds)
- **BLE RSSI**: Bluetooth signal strength (diagnostic, disabled by default)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/xxddff/linptech_ble`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Linptech BLE" and install

### Manual Installation

1. Download the `custom_components/linptech_ble` folder from this repository
2. Copy the folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Prerequisites

Before configuring the integration, you need:

1. **MAC Address**: The Bluetooth MAC address of your Linptech device
2. **Bindkey**: A 32-character hexadecimal encryption key

### How to Obtain the Bindkey

[home assistant document](https://www.home-assistant.io/integrations/xiaomi_ble/#encryption)

2. **BLE Monitor Integration**: Use the Home Assistant BLE Monitor integration to capture and display bindkeys

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Linptech BLE**
4. Enter the following information:
   - **MAC Address**: Your device's Bluetooth MAC address (format: `AA:BB:CC:DD:EE:FF`)
   - **Bindkey**: Your 32-character hexadecimal bindkey

5. Click **Submit**

The integration will automatically discover and create entities for your device.

## Troubleshooting

### Device Not Found

- Ensure Bluetooth is enabled on your Home Assistant host
- Verify the device is within Bluetooth range
- Check that the MAC address is correct and formatted properly
- Ensure your Home Assistant has Bluetooth capabilities (some installation methods may not include Bluetooth support)

### Entities Not Updating

- Verify the bindkey is correct (32 hexadecimal characters)
- Check Home Assistant logs for decryption errors
- Ensure the device has fresh batteries
- Move the device closer to your Bluetooth adapter

### Invalid Bindkey Error

If you see "Invalid bindkey format" in the logs:
- Ensure the bindkey contains only hexadecimal characters (0-9, A-F)
- Verify it's exactly 32 characters long (16 bytes in hex)
- Remove any spaces, dashes, or special characters

## Technical Details

### Protocol

This integration implements a custom parser for:
- **MiBeacon Protocol**: Xiaomi's BLE advertisement protocol (v4/v5)
- **AES-CCM Encryption**: Secure decryption of device data
- **Passive BLE Scanning**: Efficient monitoring without active connections

### Architecture

The integration uses Home Assistant's `PassiveBluetoothProcessorCoordinator` for efficient BLE data processing, ensuring minimal resource usage and fast response times.

## Development

This integration is built using:
- Home Assistant's Bluetooth integration
- Passive Bluetooth data processors
- Config flow for easy setup

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with a clear description

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Protocol information derived from public MiBeacon documentation
- Inspired by the open-source Xiaomi BLE ecosystem
- Device support information from [ble_monitor](https://github.com/custom-components/ble_monitor)

## Support

- **Issues**: [GitHub Issues](https://github.com/xxddff/linptech_ble/issues)
- **Documentation**: [GitHub Repository](https://github.com/xxddff/linptech_ble)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## Changelog

### Version 0.1.0
- Initial release
- Support for Linptech PS1BB pressure sensor
- MiBeacon v4/v5 decryption
- Binary sensor for pressure state
- Sensors for battery, duration metrics, and RSSI
