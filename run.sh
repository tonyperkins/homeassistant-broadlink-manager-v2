#!/usr/bin/with-contenv bashio

# ==============================================================================
# Home Assistant Add-on: Broadlink Manager v2
# Runs the Broadlink Manager application
# ==============================================================================

# Wait for Home Assistant to start
bashio::log.info "Starting Broadlink Manager v2..."

# Get configuration options with defaults
LOG_LEVEL=$(bashio::config 'log_level' 'info')
WEB_PORT=$(bashio::config 'web_port' '8099')
AUTO_DISCOVER=$(bashio::config 'auto_discover' 'true')

# Validate and set defaults if null/empty
if [ -z "${LOG_LEVEL}" ] || [ "${LOG_LEVEL}" = "null" ]; then
    LOG_LEVEL="info"
fi

if [ -z "${WEB_PORT}" ] || [ "${WEB_PORT}" = "null" ]; then
    WEB_PORT="8099"
fi

if [ -z "${AUTO_DISCOVER}" ] || [ "${AUTO_DISCOVER}" = "null" ]; then
    AUTO_DISCOVER="true"
fi

# Set log level
bashio::log.info "Setting log level to: ${LOG_LEVEL}"
export LOG_LEVEL

# Set configuration environment variables
export WEB_PORT
export AUTO_DISCOVER

# Print configuration
bashio::log.info "Configuration:"
bashio::log.info "- Log Level: ${LOG_LEVEL}"
bashio::log.info "- Web Port: ${WEB_PORT}"
bashio::log.info "- Auto Discover: ${AUTO_DISCOVER}"

# Start the application
bashio::log.info "Starting Broadlink Manager application..."
cd /app || bashio::exit.nok "Cannot change to application directory"

# Run the main application
exec python3 main.py
