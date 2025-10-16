# Broadlink Manager API Reference

**Version:** 2.0  
**Last Updated:** October 15, 2025

This document describes the REST API endpoints provided by the Broadlink Manager add-on.

---

## Base URL

When running as a Home Assistant add-on:
```
http://homeassistant.local:8099
```

Replace `homeassistant.local` with your Home Assistant IP address if needed.

## Authentication

Currently, the API does not require authentication as it's designed to run within your local network.

---

## Table of Contents

- [Device Management](#device-management)
- [Managed Devices](#managed-devices)
- [Command Management](#command-management)
- [Area Management](#area-management)
- [SmartIR Integration](#smartir-integration)
- [Broadlink Devices](#broadlink-devices)
- [Error Responses](#error-responses)

---

## Device Management

### List All Devices

Get all managed devices (legacy endpoint).

**Endpoint:** `GET /api/devices`

**Response:**
```json
{
  "devices": [
    {
      "id": "living_room_fan",
      "name": "Living Room Fan",
      "device_type": "broadlink",
      "broadlink_entity": "remote.living_room_rm4_pro",
      "area": "Living Room",
      "commands": {
        "turn_on": "fan_on",
        "turn_off": "fan_off"
      },
      "command_count": 2
    }
  ],
  "count": 1
}
```

---

### Get Specific Device

Get details for a specific device.

**Endpoint:** `GET /api/devices/<device_id>`

**Response:**
```json
{
  "id": "living_room_fan",
  "name": "Living Room Fan",
  "device_type": "broadlink",
  "broadlink_entity": "remote.living_room_rm4_pro",
  "area": "Living Room",
  "commands": {
    "turn_on": "fan_on",
    "turn_off": "fan_off"
  },
  "command_count": 2
}
```

---

### Create Device

Create a new device (legacy endpoint).

**Endpoint:** `POST /api/devices`

**Request Body:**
```json
{
  "device_id": "bedroom_fan",
  "device_name": "Bedroom Fan",
  "device_type": "broadlink",
  "broadlink_entity": "remote.bedroom_rm4_pro",
  "area": "Bedroom",
  "commands": {
    "turn_on": "fan_on",
    "turn_off": "fan_off"
  }
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "bedroom_fan",
  "message": "Device created successfully"
}
```

---

### Update Device

Update an existing device.

**Endpoint:** `PUT /api/devices/<device_id>`

**Request Body:**
```json
{
  "device_name": "Bedroom Ceiling Fan",
  "area": "Master Bedroom",
  "commands": {
    "turn_on": "fan_on",
    "turn_off": "fan_off",
    "speed_1": "fan_speed_1"
  }
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "bedroom_fan",
  "message": "Device updated successfully"
}
```

---

### Delete Device

Delete a device.

**Endpoint:** `DELETE /api/devices/<device_id>`

**Response:**
```json
{
  "success": true,
  "message": "Device deleted successfully"
}
```

---

### Find Broadlink Owner

Find which Broadlink device owns a specific device's commands.

**Endpoint:** `POST /api/devices/find-broadlink-owner`

**Request Body:**
```json
{
  "device_name": "samsung_model1"
}
```

**Response:**
```json
{
  "device_name": "samsung_model1",
  "broadlink_entity": "remote.master_bedroom_rm4_pro",
  "broadlink_name": "Master Bedroom RM4 Pro"
}
```

---

### Discover Untracked Devices

Discover devices that exist in Broadlink storage but are not tracked in metadata.

**Endpoint:** `GET /api/devices/discover`

**Response:**
```json
{
  "untracked_devices": [
    {
      "device_name": "samsung_model1",
      "command_count": 5,
      "commands": ["turn_on", "turn_off", "volume_up", "volume_down", "mute"]
    }
  ],
  "count": 1
}
```

---

### Delete Untracked Device

Delete all commands for an untracked device from Broadlink storage.

**Endpoint:** `DELETE /api/devices/untracked/<device_name>`

**Response:**
```json
{
  "success": true,
  "message": "Deleted 5 commands for device samsung_model1",
  "deleted_commands": ["turn_on", "turn_off", "volume_up", "volume_down", "mute"]
}
```

---

## Managed Devices

### Create Managed Device

Create a new managed device (supports both Broadlink and SmartIR types).

**Endpoint:** `POST /api/devices/managed`

**Request Body (Broadlink):**
```json
{
  "device_name": "Samsung TV",
  "device": "samsung_model1",
  "device_type": "broadlink",
  "broadlink_entity": "remote.master_bedroom_rm4_pro",
  "area": "Master Bedroom",
  "commands": {
    "turn_on": "turn_on",
    "turn_off": "turn_off",
    "volume_up": "volume_up"
  }
}
```

**Request Body (SmartIR):**
```json
{
  "device_name": "Living Room AC",
  "device": "climate.living_room_ac",
  "device_type": "smartir",
  "area": "Living Room",
  "smartir_config": {
    "platform": "climate",
    "code_id": 1080,
    "manufacturer": "Samsung",
    "model": "AR09FSSEDWUNEU"
  }
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "samsung_model1",
  "message": "Device created successfully"
}
```

---

### List Managed Devices

Get all managed devices from device manager.

**Endpoint:** `GET /api/devices/managed`

**Response:**
```json
{
  "devices": [
    {
      "id": "samsung_model1",
      "name": "Samsung TV",
      "device_type": "broadlink",
      "broadlink_entity": "remote.master_bedroom_rm4_pro",
      "area": "Master Bedroom",
      "commands": {
        "turn_on": "turn_on",
        "turn_off": "turn_off"
      },
      "command_count": 2,
      "created_at": "2025-10-15T19:30:00Z"
    }
  ],
  "count": 1
}
```

---

### Get Managed Device

Get a specific managed device.

**Endpoint:** `GET /api/devices/managed/<device_id>`

**Response:**
```json
{
  "id": "samsung_model1",
  "name": "Samsung TV",
  "device_type": "broadlink",
  "broadlink_entity": "remote.master_bedroom_rm4_pro",
  "area": "Master Bedroom",
  "commands": {
    "turn_on": "turn_on",
    "turn_off": "turn_off"
  },
  "command_count": 2,
  "created_at": "2025-10-15T19:30:00Z"
}
```

---

### Update Managed Device

Update a managed device.

**Endpoint:** `PUT /api/devices/managed/<device_id>`

**Request Body:**
```json
{
  "device_name": "Samsung Smart TV",
  "area": "Living Room",
  "commands": {
    "turn_on": "turn_on",
    "turn_off": "turn_off",
    "volume_up": "volume_up",
    "volume_down": "volume_down"
  }
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "samsung_model1",
  "message": "Device updated successfully"
}
```

---

### Delete Managed Device

Delete a managed device and optionally its commands from Broadlink storage.

**Endpoint:** `DELETE /api/devices/managed/<device_id>`

**Request Body:**
```json
{
  "delete_commands": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device samsung_model1 deleted",
  "commands_deleted": true
}
```

---

## Command Management

### Learn Command

Learn a new IR/RF command.

**Endpoint:** `POST /api/commands/learn`

**Request Body:**
```json
{
  "entity_id": "remote.master_bedroom_rm4_pro",
  "device": "samsung_model1",
  "command": "turn_on",
  "command_type": "ir"
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ Command 'turn_on' learned successfully! (May take a moment to appear)",
  "code": "pending"
}
```

**Note:** The command will appear in Broadlink storage after 10-30 seconds due to Home Assistant's async storage writes.

---

### Test Command

Send a learned command to test it.

**Endpoint:** `POST /api/commands/test`

**Request Body:**
```json
{
  "entity_id": "remote.master_bedroom_rm4_pro",
  "device": "samsung_model1",
  "command": "turn_on"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Command sent successfully"
}
```

---

### Delete Command

Delete a learned command.

**Endpoint:** `DELETE /api/commands/<device_id>/<command_name>`

**Response:**
```json
{
  "success": true,
  "message": "Command 'turn_on' deleted from device 'samsung_model1'"
}
```

---

### Get Device Commands

Get all commands for a device.

**Endpoint:** `GET /api/commands/<device_id>`

**Response:**
```json
{
  "device_id": "samsung_model1",
  "commands": {
    "turn_on": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIU...",
    "turn_off": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIU...",
    "volume_up": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIU..."
  },
  "count": 3
}
```

---

### Get Broadlink Commands

Get learned commands from Broadlink storage files.

**Endpoint:** `GET /api/commands/broadlink/<device_name>`

**Response:**
```json
{
  "device_name": "samsung_model1",
  "commands": {
    "turn_on": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIU...",
    "turn_off": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIU..."
  },
  "count": 2
}
```

---

### Get Untracked Commands

Get commands that exist in Broadlink storage but not in metadata.

**Endpoint:** `GET /api/commands/untracked`

**Response:**
```json
{
  "untracked_commands": {
    "samsung_model1": {
      "turn_on": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIU...",
      "turn_off": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIU..."
    }
  },
  "count": 2
}
```

---

### Import Commands

Import untracked commands into a device's metadata.

**Endpoint:** `POST /api/commands/import`

**Request Body:**
```json
{
  "device_id": "samsung_model1",
  "commands": ["turn_on", "turn_off", "volume_up"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Imported 3 commands into device samsung_model1",
  "imported_count": 3
}
```

---

## Area Management

### List Areas

Get all available areas from Home Assistant.

**Endpoint:** `GET /api/areas`

**Response:**
```json
{
  "areas": [
    "Living Room",
    "Bedroom",
    "Kitchen",
    "Master Bedroom"
  ]
}
```

---

## SmartIR Integration

### Get SmartIR Status

Get SmartIR installation status.

**Endpoint:** `GET /api/smartir/status`

**Response:**
```json
{
  "installed": true,
  "version": "1.17.9",
  "codes_path": "/config/custom_components/smartir/codes",
  "platforms": ["climate", "media_player", "fan"]
}
```

---

### Get SmartIR Platforms

Get available SmartIR platforms.

**Endpoint:** `GET /api/smartir/platforms`

**Response:**
```json
{
  "installed": true,
  "platforms": ["climate", "media_player", "fan", "light"]
}
```

---

### Get Platform Codes

Get available code files for a specific platform.

**Endpoint:** `GET /api/smartir/platforms/<platform>/codes`

**Response:**
```json
{
  "platform": "climate",
  "codes": [
    {
      "code_id": 1000,
      "manufacturer": "Gree",
      "supported_models": ["YAA1FBF", "YB1F2"]
    },
    {
      "code_id": 1080,
      "manufacturer": "Samsung",
      "supported_models": ["AR09FSSEDWUNEU"]
    }
  ],
  "count": 2
}
```

---

### Get Code Details

Get details for a specific code file.

**Endpoint:** `GET /api/smartir/platforms/<platform>/codes/<code_id>`

**Response:**
```json
{
  "code_id": 1080,
  "manufacturer": "Samsung",
  "supportedModels": ["AR09FSSEDWUNEU", "AR12FSSEDWUNEU"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "minTemperature": 16,
  "maxTemperature": 30,
  "precision": 1,
  "operationModes": ["auto", "cool", "dry", "fan_only", "heat"],
  "fanModes": ["auto", "low", "medium", "high"]
}
```

---

### Search Codes

Search for SmartIR codes by manufacturer or model.

**Endpoint:** `GET /api/smartir/search?platform=<platform>&query=<query>`

**Query Parameters:**
- `platform` - Platform to search (climate, media_player, fan, light)
- `query` - Search term (manufacturer or model)

**Response:**
```json
{
  "results": [
    {
      "code_id": 1080,
      "manufacturer": "Samsung",
      "supported_models": ["AR09FSSEDWUNEU"],
      "platform": "climate"
    }
  ],
  "count": 1
}
```

---

### Get Manufacturers

Get list of manufacturers for a platform.

**Endpoint:** `GET /api/smartir/platforms/<platform>/manufacturers`

**Response:**
```json
{
  "platform": "climate",
  "manufacturers": [
    "Gree",
    "Samsung",
    "LG",
    "Daikin",
    "Mitsubishi"
  ],
  "count": 5
}
```

---

### Get Models by Manufacturer

Get models for a specific manufacturer.

**Endpoint:** `GET /api/smartir/platforms/<platform>/manufacturers/<manufacturer>/models`

**Response:**
```json
{
  "platform": "climate",
  "manufacturer": "Samsung",
  "models": [
    {
      "code_id": 1080,
      "supported_models": ["AR09FSSEDWUNEU", "AR12FSSEDWUNEU"]
    },
    {
      "code_id": 1081,
      "supported_models": ["AR18FSSEDWUNEU"]
    }
  ],
  "count": 2
}
```

---

## Broadlink Devices

### Get Broadlink Devices

Get available Broadlink devices from Home Assistant.

**Endpoint:** `GET /api/broadlink/devices`

**Response:**
```json
{
  "devices": [
    {
      "entity_id": "remote.master_bedroom_rm4_pro",
      "name": "Master Bedroom RM4 Pro",
      "state": "idle",
      "type": "RM4 Pro"
    },
    {
      "entity_id": "remote.living_room_rm_mini",
      "name": "Living Room RM Mini",
      "state": "idle",
      "type": "RM Mini 3"
    }
  ]
}
```

---

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Command Naming Conventions

For best results with entity auto-detection, use these naming patterns:

### Lights
- `light_on`, `light_off` - Separate on/off commands
- `light_toggle` - Single toggle command

### Fans
- `fan_speed_1` through `fan_speed_6` - Speed levels
- `fan_off` - Turn off
- `fan_reverse` - Reverse direction

### Media Players
- `power` - Power toggle
- `volume_up`, `volume_down` - Volume control
- `mute` - Mute toggle
- `play`, `pause`, `stop` - Playback control
- `channel_up`, `channel_down` - Channel control

---

## Storage Latency

**Important:** Home Assistant's Broadlink storage has a write latency of 10-30 seconds. After learning a command:

1. The API returns success immediately
2. The command appears in storage after 10-30 seconds
3. Testing the command works once it's in storage

This is normal behavior and handled automatically by the application.

---

## Examples

### Complete Device Adoption Workflow

1. **Discover untracked devices:**
```bash
curl http://homeassistant.local:8099/api/devices/discover
```

2. **Find Broadlink owner:**
```bash
curl -X POST http://homeassistant.local:8099/api/devices/find-broadlink-owner \
  -H "Content-Type: application/json" \
  -d '{"device_name": "samsung_model1"}'
```

3. **Create managed device:**
```bash
curl -X POST http://homeassistant.local:8099/api/devices/managed \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Samsung TV",
    "device": "samsung_model1",
    "device_type": "broadlink",
    "broadlink_entity": "remote.master_bedroom_rm4_pro",
    "area": "Master Bedroom",
    "commands": {
      "turn_on": "turn_on",
      "turn_off": "turn_off"
    }
  }'
```

---

### SmartIR Device Creation

1. **Search for device code:**
```bash
curl "http://homeassistant.local:8099/api/smartir/search?platform=climate&query=Samsung"
```

2. **Get code details:**
```bash
curl http://homeassistant.local:8099/api/smartir/platforms/climate/codes/1080
```

3. **Create SmartIR device:**
```bash
curl -X POST http://homeassistant.local:8099/api/devices/managed \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Living Room AC",
    "device": "climate.living_room_ac",
    "device_type": "smartir",
    "area": "Living Room",
    "smartir_config": {
      "platform": "climate",
      "code_id": 1080,
      "manufacturer": "Samsung",
      "model": "AR09FSSEDWUNEU"
    }
  }'
```

---

## Support

For issues or questions about the API:
- Check the [Data Model documentation](DATA_MODEL.md)
- Review [Architecture documentation](ARCHITECTURE.md)
- Open an [issue on GitHub](https://github.com/tonyperkins/homeassistant-broadlink-manager/issues)
