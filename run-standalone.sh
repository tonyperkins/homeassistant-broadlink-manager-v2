#!/bin/bash
# ==============================================================================
# Broadlink Manager - Standalone Docker Mode
# Runs the Broadlink Manager application without Home Assistant Supervisor
# ==============================================================================

set -e

echo "=========================================="
echo "Broadlink Manager - Standalone Mode"
echo "=========================================="

# Validate required environment variables
if [ -z "$HA_TOKEN" ]; then
    echo "ERROR: HA_TOKEN environment variable is required"
    echo "Please create a long-lived access token in Home Assistant:"
    echo "  1. Go to your Home Assistant profile"
    echo "  2. Scroll to 'Long-Lived Access Tokens'"
    echo "  3. Click 'Create Token'"
    echo "  4. Copy the token and set it as HA_TOKEN environment variable"
    exit 1
fi

if [ -z "$HA_URL" ]; then
    echo "WARNING: HA_URL not set, using default: http://localhost:8123"
    export HA_URL="http://localhost:8123"
fi

# Set default values for optional variables
export LOG_LEVEL="${LOG_LEVEL:-info}"
export WEB_PORT="${WEB_PORT:-8099}"
export AUTO_DISCOVER="${AUTO_DISCOVER:-true}"
export CONFIG_PATH="${CONFIG_PATH:-/config}"

# Print configuration
echo ""
echo "Configuration:"
echo "  Home Assistant URL: $HA_URL"
echo "  Log Level: $LOG_LEVEL"
echo "  Web Port: $WEB_PORT"
echo "  Auto Discover: $AUTO_DISCOVER"
echo "  Config Path: $CONFIG_PATH"
echo "  Token: ${HA_TOKEN:0:20}..." # Show first 20 chars only
echo ""

# Validate config path exists
if [ ! -d "$CONFIG_PATH" ]; then
    echo "ERROR: Config path does not exist: $CONFIG_PATH"
    echo "Please mount your Home Assistant config directory to /config"
    echo "Example: docker run -v /path/to/ha/config:/config ..."
    exit 1
fi

echo "Starting Broadlink Manager application..."
echo "=========================================="
echo ""

# Change to application directory
cd /app || exit 1

# Run the main application
exec python3 main.py
