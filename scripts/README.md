# Scripts

This directory contains utility scripts for maintaining Broadlink Manager.

## generate_device_index.py

Generates a searchable index of all device codes from the SmartIR Code Aggregator database.

### Purpose

The device index allows Broadlink Manager to:
- Load manufacturer/model lists instantly (no GitHub API calls)
- Avoid GitHub API rate limits
- Work offline with cached data
- Provide fast autocomplete in the UI
- Access codes from multiple sources (SmartIR, IRDB, etc.)

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
- **After updating** the smartir-code-aggregator repository
- **Periodically** (monthly/quarterly) to get new devices from aggregated sources
- **Before releases** to ensure index is up-to-date

### Output

Creates `smartir_device_index.json` with structure:

```json
{
  "version": "1.0.0",
  "last_updated": "2025-10-16T17:00:00Z",
  "source": "https://github.com/tonyperkins/smartir-code-aggregator",
  "description": "Aggregated IR/RF codes from SmartIR, IRDB, and other sources",
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
- The aggregator's `codes/` directory is updated
- Manually triggered via GitHub Actions
- Monthly (first day of each month)

The workflow will:
1. Run the generator script
2. Commit `smartir_device_index.json` if changed
3. Push to the repository

## Notes

- The index file is **bundled with Broadlink Manager** (not fetched from GitHub)
- Users can manually update via **Settings → Update Device Index**
- The GitHub Action keeps the aggregator's index up-to-date automatically
- No automatic refresh - updates are manual or via GitHub Action only
- The aggregator combines codes from SmartIR, IRDB, and other sources

## update_reddit_post.py

Updates Reddit posts programmatically with the latest Broadlink Manager information.

### Purpose

Automatically update Reddit announcement posts with:
- Latest features and capabilities
- Current changelog/release notes
- Installation instructions
- Links to documentation
- Auto-generated timestamp

### Setup

1. **Create a Reddit App** at https://www.reddit.com/prefs/apps
   - Choose "script" as the app type
   - Note your client_id and client_secret

2. **Set Environment Variables** (see `.env.example`):
   ```bash
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USERNAME=your_username
   REDDIT_PASSWORD=your_password
   REDDIT_USER_AGENT=BroadlinkManager:v2.0:script (by /u/YourUsername)
   ```

3. **Install Dependencies**:
   ```bash
   pip install praw
   ```

### Usage

**Preview content (dry run)**:
```bash
python scripts/update_reddit_post.py --dry-run
```

**Update a post**:
```bash
python scripts/update_reddit_post.py abc123
```
Replace `abc123` with your Reddit post ID from the URL.

### Automation

You can automate updates via:
- **GitHub Actions** - Update on releases
- **Cron Jobs** - Scheduled updates (weekly/monthly)
- **Manual** - Run after major changes

See `docs/REDDIT_UPDATES.md` for detailed setup and automation examples.

### Limitations

- Can only edit self-posts (text posts), not link posts
- Cannot change post title after creation
- Must be the post author
- Rate limited to 60 requests/minute

### Documentation

Full documentation: `docs/REDDIT_UPDATES.md`

## validate_yaml.py

Validates SmartIR YAML configuration files to prevent Home Assistant boot failures.

### Purpose

The YAML validator ensures that SmartIR configuration files are valid before they're written to disk. This prevents Home Assistant from booting in safe mode due to configuration errors.

### Usage

**Validate a single file**:
```bash
python scripts/validate_yaml.py /config/smartir/climate.yaml
```

**Validate entire directory**:
```bash
python scripts/validate_yaml.py /config/smartir/
```

**Specify platform explicitly**:
```bash
python scripts/validate_yaml.py /config/smartir/climate.yaml climate
```

### What It Validates

- **Required fields**: platform, name, unique_id, device_code, controller_data
- **Data types**: Ensures fields have correct types (int, str, etc.)
- **Entity IDs**: Validates Home Assistant entity ID format
- **unique_id format**: Checks for lowercase, no spaces
- **device_code**: Must be positive integer
- **YAML syntax**: Ensures file is valid YAML
- **Duplicate detection**: Prevents duplicate unique_ids

### Output

**Valid file**:
```
🔍 Validating /config/smartir/climate.yaml as climate platform...

✅ YAML file is valid!
```

**Invalid file**:
```
🔍 Validating /config/smartir/climate.yaml as climate platform...

❌ YAML file validation failed:

   • Device 0 (Living Room AC): Missing required field: device_code
   • Device 1 (Bedroom AC): Invalid entity ID format for 'controller_data'
```

### Automatic Validation

Validation happens automatically when:
- Creating new SmartIR devices
- Updating existing devices
- Generating entity helpers

The validator creates `.backup` files before modifying YAML, allowing recovery if issues occur.

### Documentation

Full documentation: `docs/YAML_VALIDATION.md`
