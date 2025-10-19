# YAML Validation System

## Overview

The Broadlink Manager includes a comprehensive YAML validation system to prevent invalid SmartIR configurations from being written to Home Assistant. This prevents HA from booting in safe mode due to configuration errors.

## Features

### Automatic Validation
- **Pre-write validation**: All YAML files are validated before being written to disk
- **Schema validation**: Checks required fields, data types, and format
- **Syntax validation**: Ensures YAML is properly formatted
- **Entity ID validation**: Validates Home Assistant entity ID format
- **Duplicate detection**: Prevents duplicate unique_ids

### Backup System
- **Automatic backups**: Creates `.backup` files before modifying YAML
- **Recovery**: Can restore from backup if validation fails
- **No data loss**: Original file preserved if new content is invalid

### Error Reporting
- **Detailed errors**: Specific error messages for each validation failure
- **Multiple errors**: Reports all validation issues at once
- **API errors**: Returns validation errors to frontend for user feedback

## Validation Rules

### Required Fields (All Platforms)
- `platform`: Must be "smartir"
- `name`: Device name (string)
- `unique_id`: Unique identifier (lowercase, numbers, underscores only)
- `device_code`: SmartIR device code (positive integer)
- `controller_data`: Remote entity ID (e.g., "remote.bedroom_rm4")

### Optional Fields by Platform

#### Climate
- `temperature_sensor`: Entity ID for temperature sensor
- `humidity_sensor`: Entity ID for humidity sensor
- `power_sensor`: Entity ID for power sensor

#### Media Player
- `power_sensor`: Entity ID for power sensor
- `source_names`: Dictionary mapping source names

#### Fan
- `power_sensor`: Entity ID for power sensor

#### Light
- `power_sensor`: Entity ID for power sensor

### Data Type Validation
- **Strings**: name, unique_id, controller_data, sensors
- **Integers**: device_code (must be positive)
- **Entity IDs**: Must follow format `domain.entity_name` (e.g., `remote.bedroom_rm4`)

### Format Validation
- **unique_id**: Only lowercase letters, numbers, and underscores
- **Entity IDs**: Must match pattern `[a-z]+\.[a-z0-9_]+`
- **device_code**: Must be positive integer

## Usage

### Automatic Validation (Built-in)

Validation happens automatically when:
1. Creating a new SmartIR device
2. Updating an existing device
3. Generating entity helpers

No user action required - validation is transparent.

### Manual Validation (CLI Tool)

Validate existing YAML files using the CLI tool:

```bash
# Validate single file
python scripts/validate_yaml.py /config/smartir/climate.yaml

# Validate entire directory
python scripts/validate_yaml.py /config/smartir/

# Specify platform explicitly
python scripts/validate_yaml.py /config/smartir/climate.yaml climate
```

### Validation Output

**Valid file:**
```
🔍 Validating /config/smartir/climate.yaml as climate platform...

✅ YAML file is valid!
```

**Invalid file:**
```
🔍 Validating /config/smartir/climate.yaml as climate platform...

❌ YAML file validation failed:

   • Device 0 (Living Room AC): Missing required field: device_code
   • Device 1 (Bedroom AC): Field 'device_code' must be int, got str: "1000"
   • Device 2 (Office AC): Invalid entity ID format for 'controller_data': remote.bedroom rm4
```

## Error Messages

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Missing required field: device_code | device_code not specified | Add device_code to configuration |
| Field 'device_code' must be int | device_code is string | Remove quotes: `device_code: 1000` |
| device_code must be positive | device_code is 0 or negative | Use positive integer |
| unique_id cannot contain spaces | unique_id has spaces | Use underscores: `living_room_ac` |
| Invalid entity ID format | Entity ID malformed | Use format: `domain.entity_name` |
| Duplicate unique_id found | Two devices have same unique_id | Make unique_ids unique |
| Platform must be 'smartir' | Wrong platform value | Set `platform: smartir` |

## Backup and Recovery

### Automatic Backups

Before writing any YAML file, a backup is created:
- **Location**: Same directory as original file
- **Naming**: `{filename}.yaml.backup`
- **Example**: `climate.yaml.backup`

### Manual Recovery

If a file becomes corrupted:

```bash
# Restore from backup
cp /config/smartir/climate.yaml.backup /config/smartir/climate.yaml

# Validate restored file
python scripts/validate_yaml.py /config/smartir/climate.yaml
```

## Integration with Frontend

### Error Display

When validation fails, the frontend displays:
1. **Error toast**: Brief error notification
2. **Detailed errors**: List of all validation issues
3. **Field highlighting**: Invalid fields highlighted in form

### Example Error Response

```json
{
  "success": false,
  "error": "Device configuration validation failed:\n  - Missing required field: device_code\n  - Invalid entity ID format for 'controller_data': remote.bedroom rm4",
  "validation_errors": [
    "Missing required field: device_code",
    "Invalid entity ID format for 'controller_data': remote.bedroom rm4"
  ]
}
```

## Technical Details

### Validation Flow

```
1. User creates/updates device
   ↓
2. Frontend sends device config to API
   ↓
3. API validates device config
   ↓
4. If valid: Read existing YAML file
   ↓
5. Add/update device in list
   ↓
6. Validate entire file content
   ↓
7. Generate YAML string
   ↓
8. Validate YAML syntax
   ↓
9. Create backup of existing file
   ↓
10. Write validated YAML to file
    ↓
11. Return success to frontend
```

### Validation Classes

**YAMLValidator** (`app/yaml_validator.py`):
- `validate_device_config()`: Validate single device
- `validate_yaml_file_content()`: Validate list of devices
- `validate_yaml_syntax()`: Validate YAML syntax
- `validate_and_format_yaml()`: Generate and validate YAML string
- `validate_existing_file()`: Validate file on disk

**SmartIRYAMLGenerator** (`app/smartir_yaml_generator.py`):
- Uses YAMLValidator before writing files
- Creates backups automatically
- Returns detailed error messages

## Troubleshooting

### HA Boots in Safe Mode

If HA boots in safe mode after adding a device:

1. **Check HA logs** for YAML errors:
   ```
   Settings → System → Logs
   ```

2. **Validate the file**:
   ```bash
   python scripts/validate_yaml.py /config/smartir/climate.yaml
   ```

3. **Restore from backup**:
   ```bash
   cp /config/smartir/climate.yaml.backup /config/smartir/climate.yaml
   ```

4. **Check configuration** in HA:
   ```
   Developer Tools → YAML → Check Configuration
   ```

### Validation Passes but HA Still Fails

If validation passes but HA still reports errors:

1. **Check SmartIR integration** is installed
2. **Verify device code** exists in SmartIR database
3. **Check controller entity** exists in HA
4. **Verify sensor entities** exist (if specified)
5. **Check HA logs** for specific error messages

### False Positives

If validator reports errors for valid configuration:

1. **Check SmartIR version** - newer versions may have different requirements
2. **Report issue** on GitHub with example configuration
3. **Manually validate** with HA's built-in validator

## Best Practices

### Device Configuration

1. **Use lowercase unique_ids**: `living_room_ac` not `Living Room AC`
2. **Verify entity IDs**: Check entity exists before adding
3. **Test device codes**: Use SmartIR profile browser to verify codes
4. **Add sensors gradually**: Start without sensors, add later if needed

### File Management

1. **Keep backups**: Don't delete `.backup` files
2. **Validate before restart**: Run validator before restarting HA
3. **Use version control**: Git track your YAML files
4. **Test in dev environment**: Test new devices in test HA instance first

### Error Handling

1. **Read error messages**: Validation errors are specific and actionable
2. **Fix all errors**: Address all validation issues before retrying
3. **Check logs**: Backend logs have detailed validation output
4. **Report bugs**: If validation is incorrect, report on GitHub

## API Reference

### Validate Device Config

```python
from yaml_validator import YAMLValidator

is_valid, errors = YAMLValidator.validate_device_config(
    config={
        "platform": "smartir",
        "name": "Living Room AC",
        "unique_id": "living_room_ac",
        "device_code": 1000,
        "controller_data": "remote.bedroom_rm4"
    },
    platform="climate"
)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

### Validate YAML File

```python
from yaml_validator import YAMLValidator

is_valid, errors = YAMLValidator.validate_existing_file(
    file_path="/config/smartir/climate.yaml",
    platform="climate"
)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

### Generate Validated YAML

```python
from yaml_validator import YAMLValidator

devices = [
    {
        "platform": "smartir",
        "name": "Living Room AC",
        "unique_id": "living_room_ac",
        "device_code": 1000,
        "controller_data": "remote.bedroom_rm4"
    }
]

is_valid, yaml_string, errors = YAMLValidator.validate_and_format_yaml(
    devices=devices,
    platform="climate"
)

if is_valid:
    with open("/config/smartir/climate.yaml", "w") as f:
        f.write(yaml_string)
```

## Future Enhancements

- [ ] Real-time validation in frontend forms
- [ ] Auto-fix common issues (e.g., convert spaces to underscores)
- [ ] Validate against SmartIR schema from GitHub
- [ ] Check if device_code exists in SmartIR database
- [ ] Verify entity IDs exist in Home Assistant
- [ ] Suggest corrections for common mistakes
- [ ] Integration with HA's built-in validator
- [ ] Pre-commit hook for YAML validation

## Related Documentation

- [SmartIR Integration](SMARTIR_INTEGRATION.md)
- [Backup and Recovery](../BACKUP_RECOVERY.md)
- [API Documentation](API.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
