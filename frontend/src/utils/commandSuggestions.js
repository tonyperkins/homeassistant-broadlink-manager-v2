/**
 * Suggest command names already learned on the user's other devices.
 *
 * When learning commands for a device, names used on other devices of the
 * same entity type are offered in the Command Name dropdown so users with
 * several identical devices don't have to retype custom names (issue #56).
 *
 * @param {Array}  devices        All managed devices (from the devices store)
 * @param {Object} currentDevice  The device being learned for
 * @param {Array}  [exclude]      Names to omit (e.g. built-in suggestions)
 * @returns {Array<string>} Sorted, deduplicated command names
 */
export function getOtherDeviceCommands(devices, currentDevice, exclude = []) {
  if (!currentDevice || !Array.isArray(devices)) return []

  const currentType = currentDevice.entity_type
  const currentId = currentDevice.id
  const skip = new Set([
    ...Object.keys(currentDevice.commands || {}),
    ...exclude,
  ])
  const names = new Set()

  for (const device of devices) {
    if (!device || device.id === currentId) continue
    if (device.entity_type !== currentType) continue
    // Only Broadlink devices have learned commands; SmartIR devices use code files
    if (device.device_type && device.device_type !== 'broadlink') continue

    for (const name of Object.keys(device.commands || {})) {
      if (!skip.has(name)) names.add(name)
    }
  }

  return [...names].sort()
}
