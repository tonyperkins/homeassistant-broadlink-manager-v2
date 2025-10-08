# Broadlink Manager API Reference

This document describes the REST API endpoints provided by the Broadlink Manager add-on.

## Base URL

When running as a Home Assistant add-on:
```
http://homeassistant.local:8099
```

Replace `homeassistant.local` with your Home Assistant IP address if needed.

## Authentication

Currently, the API does not require authentication as it's designed to run within your local network. Future versions may add authentication support.

---

## Device Management

### List Devices

Get all available Broadlink devices.

**Endpoint:** `GET /api/devices`

**Response:**
```json
{
  "success": true,
  "devices": [
    {
      "entity_id": "remote.broadlink_rm4_pro",
      "name": "Broadlink RM4 Pro",
      "device_id": "abc123def456",
      "type": "RM4 Pro"
    }
  ]
}
```

---

## Command Management

### List Commands

Get all learned commands for a device.

**Endpoint:** `GET /api/commands`

**Query Parameters:**
- `device` (optional) - Filter by device name

**Response:**
```json
{
  "success": true,
  "commands": {
    "tony_s_office_ceiling_fan": {
      "light_on": "scAAArCeB...",
      "light_off": "scCwBLCeB...",
      "fan_speed_1": "scAAArCeB..."
    }
  }
}
```

### Learn Command

Learn a new IR/RF command.

**Endpoint:** `POST /api/learn`

**Request Body:**
```json
{
  "device_id": "abc123def456",
  "device_name": "tony_s_office_ceiling_fan",
  "command_name": "light_on"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Command learned successfully",
  "command_code": "scAAArCeB..."
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Learning timeout - no signal received"
}
```

### Test Command

Send a learned command to test it.

**Endpoint:** `POST /api/test`

**Request Body:**
```json
{
  "device_id": "abc123def456",
  "device_name": "tony_s_office_ceiling_fan",
  "command_name": "light_on"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Command sent successfully"
}
```

### Delete Command

Delete a learned command.

**Endpoint:** `DELETE /api/commands/<device_name>/<command_name>`

**Response:**
```json
{
  "success": true,
  "message": "Command deleted successfully"
}
```

---

## Area Management

### List Areas

Get all configured areas/rooms.

**Endpoint:** `GET /api/areas`

**Response:**
```json
{
  "success": true,
  "areas": [
    {
      "area_id": "tony_s_office",
      "name": "Tony's Office",
      "devices": ["tony_s_office_ceiling_fan"]
    }
  ]
}
```

### Create Area

Create a new area.

**Endpoint:** `POST /api/areas`

**Request Body:**
```json
{
  "area_id": "living_room",
  "name": "Living Room"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Area created successfully",
  "area_id": "living_room"
}
```

### Assign Device to Area

Assign a device to an area.

**Endpoint:** `POST /api/areas/<area_id>/devices`

**Request Body:**
```json
{
  "device_name": "living_room_tv"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device assigned to area"
}
```

---

## Entity Management

### List Entities

Get all configured entities with statistics.

**Endpoint:** `GET /api/entities`

**Response:**
```json
{
  "success": true,
  "entities": {
    "office_ceiling_fan_light": {
      "entity_type": "light",
      "device": "tony_s_office_ceiling_fan",
      "commands": {
        "turn_on": "light_on",
        "turn_off": "light_off"
      },
      "device_id": "abc123",
      "enabled": true,
      "friendly_name": "Office Ceiling Fan Light",
      "area": "Tony's Office"
    }
  },
  "stats": {
    "total_entities": 5,
    "entities_by_type": {
      "light": 3,
      "fan": 2
    },
    "last_generated": "2025-10-06T14:30:00"
  }
}
```

### Get Entity

Get a specific entity configuration.

**Endpoint:** `GET /api/entities/<entity_id>`

**Response:**
```json
{
  "success": true,
  "entity": {
    "entity_type": "light",
    "device": "tony_s_office_ceiling_fan",
    "commands": {
      "turn_on": "light_on",
      "turn_off": "light_off"
    },
    "enabled": true
  }
}
```

### Save Entity

Create or update an entity configuration.

**Endpoint:** `POST /api/entities`

**Request Body:**
```json
{
  "entity_id": "office_light",
  "entity_data": {
    "entity_type": "light",
    "device": "tony_s_office_ceiling_fan",
    "commands": {
      "turn_on": "light_on",
      "turn_off": "light_off"
    },
    "device_id": "abc123",
    "enabled": true,
    "friendly_name": "Office Light",
    "area": "Tony's Office"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Entity saved successfully",
  "entity_id": "office_light"
}
```

### Delete Entity

Delete an entity configuration.

**Endpoint:** `DELETE /api/entities/<entity_id>`

**Response:**
```json
{
  "success": true,
  "message": "Entity deleted successfully"
}
```

### Auto-Detect Entities

Automatically detect entities from learned commands.

**Endpoint:** `POST /api/entities/detect`

**Request Body:**
```json
{
  "device_name": "tony_s_office_ceiling_fan",
  "commands": {
    "light_on": "scAAArCeB...",
    "light_off": "scCwBLCeB...",
    "fan_speed_1": "scAAArCeB...",
    "fan_speed_2": "scAAArCeB...",
    "fan_off": "scAAArCeB..."
  },
  "area_name": "Tony's Office"
}
```

**Response:**
```json
{
  "success": true,
  "detected_entities": {
    "tony_s_office_ceiling_fan_light": {
      "entity_type": "light",
      "device": "tony_s_office_ceiling_fan",
      "commands": {
        "turn_on": "light_on",
        "turn_off": "light_off"
      },
      "friendly_name": "Tony's Office Ceiling Fan Light",
      "area": "Tony's Office",
      "auto_detected": true
    },
    "tony_s_office_ceiling_fan": {
      "entity_type": "fan",
      "device": "tony_s_office_ceiling_fan",
      "commands": {
        "turn_off": "fan_off",
        "speed_1": "fan_speed_1",
        "speed_2": "fan_speed_2"
      },
      "friendly_name": "Tony's Office Ceiling Fan",
      "area": "Tony's Office",
      "speed_count": 2,
      "auto_detected": true
    }
  },
  "count": 2
}
```

### Generate Entity Files

Generate Home Assistant YAML entity files.

**Endpoint:** `POST /api/entities/generate`

**Request Body:**
```json
{
  "device_id": "abc123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Entity files generated successfully",
  "entities_count": 5,
  "entity_counts": {
    "light": 3,
    "fan": 2
  },
  "files": {
    "entities": "/config/broadlink_manager/entities.yaml",
    "helpers": "/config/broadlink_manager/helpers.yaml",
    "readme": "/config/broadlink_manager/README.md"
  },
  "instructions": {
    "step1": "Add to configuration.yaml:",
    "code": "light: !include broadlink_manager/entities.yaml\nfan: !include broadlink_manager/entities.yaml\nswitch: !include broadlink_manager/entities.yaml\ninput_boolean: !include broadlink_manager/helpers.yaml\ninput_select: !include broadlink_manager/helpers.yaml",
    "step2": "Check configuration in Developer Tools → YAML",
    "step3": "Restart Home Assistant"
  }
}
```

### Get Entity Types

Get supported entity types and their command roles.

**Endpoint:** `GET /api/entities/types`

**Response:**
```json
{
  "success": true,
  "types": ["light", "fan", "switch", "media_player"],
  "roles": {
    "light": ["turn_on", "turn_off", "toggle"],
    "fan": ["turn_on", "turn_off", "speed_1", "speed_2", "speed_3", "speed_4", "speed_5", "speed_6", "reverse"],
    "switch": ["turn_on", "turn_off", "toggle"],
    "media_player": ["power", "volume_up", "volume_down", "mute", "play", "pause", "stop", "play_pause", "next", "previous", "channel_up", "channel_down"]
  }
}
```

---

## Storage Management

### Get Storage Info

Get information about the storage directory.

**Endpoint:** `GET /api/storage/info`

**Response:**
```json
{
  "success": true,
  "storage_path": "/config/broadlink_manager",
  "files": {
    "metadata": true,
    "entities": true,
    "helpers": true,
    "readme": true
  },
  "stats": {
    "total_entities": 5,
    "entities_by_type": {
      "light": 3,
      "fan": 2
    },
    "last_generated": "2025-10-06T14:30:00"
  }
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
- `lamp_on`, `lamp_off` - Alternative naming

### Fans
- `fan_speed_1` through `fan_speed_6` - Speed levels (numbered)
- `fan_low`, `fan_medium`, `fan_high` - Named speed levels
- `fan_off` - Turn off
- `fan_on` - Turn on (optional)
- `fan_reverse` - Reverse direction

### Switches
- `on`, `off` - Simple on/off
- `toggle` - Single toggle
- `power` - Power toggle

### Media Players
- `power` - Power toggle
- `vol_up`, `vol_down` - Volume control
- `volume_up`, `volume_down` - Alternative volume naming
- `mute` - Mute toggle
- `play`, `pause`, `stop` - Playback control
- `play_pause` - Combined play/pause
- `next`, `previous` - Track navigation
- `ch_up`, `ch_down` - Channel control
- `channel_up`, `channel_down` - Alternative channel naming

---

## Examples

### Complete Workflow Example

1. **Learn commands:**
```bash
curl -X POST http://homeassistant.local:8099/api/learn \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "abc123",
    "device_name": "office_fan",
    "command_name": "light_on"
  }'
```

2. **Auto-detect entities:**
```bash
curl -X POST http://homeassistant.local:8099/api/entities/detect \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "office_fan",
    "commands": {
      "light_on": "...",
      "light_off": "..."
    }
  }'
```

3. **Generate entity files:**
```bash
curl -X POST http://homeassistant.local:8099/api/entities/generate \
  -H "Content-Type: application/json" \
  -d '{"device_id": "abc123"}'
```

4. **Add to configuration.yaml** and restart Home Assistant

---

## WebSocket API (Future)

WebSocket support for real-time updates is planned for future versions.

---

## Rate Limiting

Currently, there is no rate limiting. Use responsibly to avoid overwhelming your Broadlink devices.

---

## Support

For issues or questions about the API:
- Check the [main documentation](README.md)
- Review [entity generation docs](ENTITY_GENERATION.md)
- Open an [issue on GitHub](https://github.com/yourusername/broadlink-manager-addon/issues)
