# Skylink Orbit Garage Door - Home Assistant Integration

A custom Home Assistant integration for **Skylink G2 garage door openers** controlled via the Orbit Home cloud service.

## Features

- **Multi-door support** - Control 3+ garage doors from a single account
- **Real-time state updates** via MQTT push notifications
- **Toggle control** - Open/close/stop garage doors
- **Easy configuration** - UI-based setup with options flow to add/remove doors
- **Auto-detection** - Account number auto-detected from login

## Requirements

- Home Assistant 2024.1 or later
- Skylink G2 garage door opener(s) with WiFi connectivity
- Orbit Home app account (the same email/password you use in the app)
- Hub IDs for each garage door controller

## Installation

### Manual Installation

1. Copy the `custom_components/skylink_orbit` folder into your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings > Devices & Services > Add Integration**
4. Search for **Skylink Orbit Garage Door**
5. Enter your Orbit Home credentials and hub IDs

### HACS Installation

1. Add this repository as a custom repository in HACS
2. Install **Skylink Orbit Garage Door**
3. Restart Home Assistant
4. Configure via **Settings > Devices & Services > Add Integration**

## Configuration

### Initial Setup

| Field | Description |
|-------|-------------|
| Email | Your Orbit Home app login email |
| Password | Your Orbit Home app password |
| Hub IDs | Comma-separated list of hub IDs (e.g., `rA8qM4QS, YAkDn9r2`) |
| Account Number | Optional - auto-detected from login |
| API URL | Advanced - leave default unless API server changes |

### Adding/Removing Doors

After initial setup, go to **Settings > Devices & Services > Skylink Orbit > Configure** to edit your hub IDs.

### Finding Your Hub IDs

Hub IDs can be found by:
- Capturing Orbit Home app traffic with a proxy tool (mitmproxy)
- Looking for `hub_id` values in the API requests

## How It Works

This integration communicates with the Skylink cloud service at `iot.skyhm.net`:

- **REST API** (port 8444) - Authentication and account management
- **MQTT** (port 1899 over SSL) - Real-time door control and state updates

Door control uses a toggle command - the same command opens or closes the door depending on its current state.

## Entities

Each hub ID creates a **Cover** entity with:
- **State**: Open / Closed / Opening / Closing
- **Actions**: Open, Close, Stop

## Troubleshooting

### "Invalid email or password"
Verify your credentials work in the Orbit Home app first.

### "Cannot connect"
Check that your Home Assistant instance can reach `iot.skyhm.net` on port 8444.

### Doors show "Unknown" state
The MQTT connection may still be initializing. Check the logs for MQTT connection status.

### Check Logs
Go to **Settings > System > Logs** and filter for `skylink_orbit` to see detailed debug information.

## Technical Details

- **IoT Class**: Cloud Push (MQTT-based real-time updates)
- **Authentication**: HMAC-MD5 signed REST API requests
- **Door Control**: MQTT publish to `skylink/things/client/{acc_no}/desire`
- **State Updates**: MQTT subscribe to `skylink/things/client/{acc_no}/get/result`

## License

MIT License - See [LICENSE](LICENSE) file.
