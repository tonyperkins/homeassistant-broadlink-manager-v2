# Scripts

Utility scripts for maintaining Broadlink Manager.

## generate_device_index.py

Generates a device index from the SmartIR device database for fast lookups.

### Purpose

Instead of scanning the entire GitHub repository every time a user opens the SmartIR device configuration, we maintain a pre-built index that lists all manufacturers, models, and device codes. This provides:

- **Instant loading** of manufacturer/model lists
- **No API rate limiting** issues
- **Better user experience** with fast UI responses
- **Offline capability** (after initial cache)

### Usage

```bash
# Install dependencies
pip install requests

# Run the generator
python scripts/generate_device_index.py
```

This will:
1. Scan all device codes in the SmartIR database
2. Extract manufacturer and model information
3. Generate `device_index.json` in the root directory
4. This file should be committed to your fork

### When to Run

Run this script:
- **After forking** SmartIR repository
- **Periodically** (monthly/quarterly) to get new devices
- **Before releases** to ensure index is up-to-date

### Output

Creates `smartir_device_index.json` with structure:

```json
{
  "version": "1.0.0",
  "last_updated": "2025-10-16T17:00:00Z",
  "source": "https://github.com/tonyperkins/smartir-device-database",
  "platforms": {
    "climate": {
      "manufacturers": {
        "Daikin": {
          "models": [
            {
              "code": "1000",
              "models": ["FTXS25CVMA"],
              "url": "https://raw.githubusercontent.com/.../1000.json"
            }
          ]
        }
      },
      "total_devices": 120
    }
  }
}
```

### Automation

A GitHub Action is included at `.github/workflows/update-smartir-index.yml` that automatically regenerates the index when:
- The fork's `codes/` directory is updated
- Manually triggered via GitHub Actions
- Monthly (first day of each month)

The workflow will:
1. Run the generator script
2. Commit `smartir_device_index.json` if changed
3. Push to the repository

## Notes

- The index file is **bundled with Broadlink Manager** (not fetched from GitHub)
- Users can manually update via **Settings → Update Device Index**
- The GitHub Action keeps the fork's index up-to-date automatically
- No automatic refresh - updates are manual or via GitHub Action only
