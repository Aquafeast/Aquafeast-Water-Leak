# Aquafeast Water Leak Sensor for Home Assistant

Custom HACS integration for **Aquafeast** Water Leak Sensor with valve control.

## Features

- Real-time leak detection
- Valve open/close control
- Automatic entity creation (Sensor + Valve)
- Easy configuration via UI
- Works with the public BRISK API

## Installation

### Via HACS (Recommended)

1. Go to **HACS** → **Integrations**
2. Click the three dots (⋮) → **Custom repositories**
3. Add this repository URL:

https://github.com/Aquafeast/Aquafeast-Water-Leak

Category: **Integration**

4. Search for **Aquafeast Water Leak** and install it
5. Restart Home Assistant

### Manual Installation

1. Download the repository
2. Copy the `custom_components/aquafeast_water_leak` folder to your HA `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Aquafeast Water Leak**
3. Fill in:
- **Name**: Friendly name for the device
- **Device ID**: Your device ID (example: `402A8F72D32A`)
- **MAC Address** (optional)
- **Scan Interval** (seconds, default 30)

## Entities Created

- **Sensor**: Leak status (Dry / Leak Detected)
- **Valve**: Main water valve (Open / Close)

## Automation Example

```yaml
automation:
- alias: "Water Leak - Shut Off Valve"
 trigger:
   - platform: state
     entity_id: binary_sensor.aquafeast_leak   # or however it appears
     to: "on"
 action:
   - service: valve.close
     target:
       entity_id: valve.aquafeast_valve
   - service: notify.mobile_app_your_phone
     data:
       message: "🚨 Water leak detected! Valve closed automatically."

**Disclaimer**
This is an unofficial integration using the public (reverse-engineered) API of the device. Use at your own risk. The API may change without notice.

**Support & Issues**
If you have problems or suggestions, please open an issue on GitHub.
