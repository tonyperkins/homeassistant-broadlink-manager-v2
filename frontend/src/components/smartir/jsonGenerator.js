/**
 * SmartIR JSON profile generator.
 *
 * Extracted as a pure module so it can be unit tested without a Vue runtime.
 * Used by SmartIRProfileBuilder.vue.
 */

/**
 * Generate a SmartIR device profile JSON object from the wizard's internal
 * profile representation.
 *
 * @param {Object} profile - Profile object from the wizard.
 * @returns {Object} SmartIR-compatible profile JSON.
 */
export function generateSmartIRJson(profile) {
  const json = {
    manufacturer: profile.manufacturer,
    supportedModels: [profile.model],
    supportedController: "Broadlink",
    commandsEncoding: "Base64",
    commandType: profile.commandType || 'ir',  // Store IR or RF type
    commands: {}
  }

  if (profile.platform === 'climate') {
    json.temperatureUnit = profile.config.temperatureUnit || 'C'
    json.minTemperature = profile.config.minTemp
    json.maxTemperature = profile.config.maxTemp
    json.precision = profile.config.precision || 1

    // Exclude 'off' from operationModes - it's a standalone command
    json.operationModes = (profile.config.modes || []).filter(mode => mode !== 'off')

    // SmartIR requires at least one fan mode - default to 'auto' if none selected
    json.fanModes = (profile.config.fanModes && profile.config.fanModes.length > 0)
      ? profile.config.fanModes
      : ['auto']

    // Add swing modes if configured
    if (profile.config.swingModes && profile.config.swingModes.length > 0) {
      json.swingModes = profile.config.swingModes
    }

    // Add preset modes if configured
    if (profile.config.presetModes && profile.config.presetModes.length > 0) {
      json.presetModes = profile.config.presetModes
    }

    // Convert flat commands to nested tree structure for climate
    // SmartIR expects: commands[mode][fan][swing][temp] = code
    // Temperature is always the leaf value (string), not an intermediate object
    const flatCommands = profile.commands || {}
    const nestedCommands = {}

    for (const [key, code] of Object.entries(flatCommands)) {
      // Handle 'off' command separately (not nested)
      if (key === 'off') {
        nestedCommands.off = code
        continue
      }

      // Parse flat key: mode_temp_fan[_swing][_preset]
      const parts = key.split('_')
      if (parts.length < 3) continue // Skip invalid keys

      const mode = parts[0]
      const temp = parts[1]
      const fan = parts[2]
      const swing = parts[3] || null
      const preset = parts[4] || null

      // Build nested structure: mode -> fan -> swing -> temp
      // Temperature is always the leaf string value
      if (!nestedCommands[mode]) nestedCommands[mode] = {}
      if (!nestedCommands[mode][fan]) nestedCommands[mode][fan] = {}

      if (swing && preset) {
        if (!nestedCommands[mode][fan][swing]) nestedCommands[mode][fan][swing] = {}
        if (!nestedCommands[mode][fan][swing][temp]) nestedCommands[mode][fan][swing][temp] = {}
        nestedCommands[mode][fan][swing][temp][preset] = code
      } else if (swing) {
        if (!nestedCommands[mode][fan][swing]) nestedCommands[mode][fan][swing] = {}
        nestedCommands[mode][fan][swing][temp] = code
      } else {
        // No swing mode: mode -> fan -> temp (temp is leaf)
        nestedCommands[mode][fan][temp] = code
      }
    }

    json.commands = nestedCommands
  } else if (profile.platform === 'fan') {
    // Convert flat UI commands back to nested SmartIR structure for fan
    // UI format: commands.turn_on, commands.turn_off, commands.speed_1, ...
    // SmartIR format: commands.default.low, commands.default.medium, ...
    const flatCommands = profile.commands || {}
    const nestedCommands = {}

    // Map UI speed names to SmartIR speed names
    const speedMapping = {
      'speed_1': 'low',
      'speed_2': 'medium',
      'speed_3': 'high'
    }

    for (const [key, code] of Object.entries(flatCommands)) {
      if (key === 'turn_off') {
        nestedCommands.off = code
      } else if (key === 'turn_on') {
        nestedCommands.on = code
      } else if (key.startsWith('speed_')) {
        const smartirSpeed = speedMapping[key] || key.replace('speed_', '')
        if (!nestedCommands.default) nestedCommands.default = {}
        nestedCommands.default[smartirSpeed] = code
      } else if (key.startsWith('oscillate_') || key.startsWith('direction_')) {
        nestedCommands[key] = code
      } else {
        nestedCommands[key] = code
      }
    }

    json.commands = nestedCommands
  } else {
    // For other platforms (media_player, light), use flat structure as-is
    json.commands = profile.commands || {}
  }

  return json
}
