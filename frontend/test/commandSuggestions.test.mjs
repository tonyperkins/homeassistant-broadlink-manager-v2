/**
 * Framework-free unit tests for the "From Your Other Devices" command
 * suggestions (issue #56).
 *
 * Run with: npm test
 * (or: node test/commandSuggestions.test.mjs)
 */

import { strict as assert } from 'node:assert'
import { test } from 'node:test'
import { getOtherDeviceCommands } from '../src/utils/commandSuggestions.js'

const fan1 = {
  id: 'bedroom_fan',
  entity_type: 'fan',
  device_type: 'broadlink',
  commands: { turn_on: 'x', fan_timer: 'x' }
}

const fan2 = {
  id: 'kitchen_fan',
  entity_type: 'fan',
  device_type: 'broadlink',
  commands: { turn_on: 'x', speed_boost: 'x' }
}

const light1 = {
  id: 'bedroom_light',
  entity_type: 'light',
  device_type: 'broadlink',
  commands: { night_mode: 'x' }
}

test('collects command names from other devices of the same entity type', () => {
  const result = getOtherDeviceCommands([fan1, fan2, light1], fan1)
  assert.deepEqual(result, ['speed_boost'])
})

test('excludes commands already learned on the current device', () => {
  const result = getOtherDeviceCommands([fan1, fan2], fan2)
  // fan1 has turn_on and fan_timer; turn_on is shared (already on fan2)
  assert.deepEqual(result, ['fan_timer'])
})

test('excludes names passed in (built-in suggestions)', () => {
  const current = { id: 'fan3', entity_type: 'fan', device_type: 'broadlink', commands: {} }
  const other = {
    id: 'fan4',
    entity_type: 'fan',
    device_type: 'broadlink',
    commands: { turn_on: 'x', turn_off: 'x', custom_speed: 'x' }
  }
  const result = getOtherDeviceCommands([current, other], current, ['turn_on', 'turn_off'])
  assert.deepEqual(result, ['custom_speed'])
})

test('ignores SmartIR devices', () => {
  const current = { id: 'fan5', entity_type: 'fan', device_type: 'broadlink', commands: {} }
  const smartirFan = {
    id: 'ac_unit',
    entity_type: 'fan',
    device_type: 'smartir',
    commands: { off: 'x', cool_24: 'x' }
  }
  const result = getOtherDeviceCommands([current, smartirFan], current)
  assert.deepEqual(result, [])
})

test('deduplicates names across multiple devices', () => {
  const current = { id: 'fan6', entity_type: 'fan', device_type: 'broadlink', commands: {} }
  const a = { id: 'a', entity_type: 'fan', device_type: 'broadlink', commands: { speed_up: 'x' } }
  const b = { id: 'b', entity_type: 'fan', device_type: 'broadlink', commands: { speed_up: 'x', speed_down: 'x' } }
  const result = getOtherDeviceCommands([current, a, b], current)
  assert.deepEqual(result, ['speed_down', 'speed_up'])
})

test('returns sorted results', () => {
  const current = { id: 'fan7', entity_type: 'fan', device_type: 'broadlink', commands: {} }
  const other = {
    id: 'fan8',
    entity_type: 'fan',
    device_type: 'broadlink',
    commands: { zeta: 'x', alpha: 'x', mid: 'x' }
  }
  const result = getOtherDeviceCommands([current, other], current)
  assert.deepEqual(result, ['alpha', 'mid', 'zeta'])
})

test('handles empty device list', () => {
  const current = { id: 'fan9', entity_type: 'fan', device_type: 'broadlink', commands: {} }
  assert.deepEqual(getOtherDeviceCommands([], current), [])
})

test('handles missing current device or devices array', () => {
  assert.deepEqual(getOtherDeviceCommands(null, fan1), [])
  assert.deepEqual(getOtherDeviceCommands([fan1], null), [])
  assert.deepEqual(getOtherDeviceCommands(undefined, undefined), [])
})

test('handles devices with no commands', () => {
  const current = { id: 'fan10', entity_type: 'fan', device_type: 'broadlink' }
  const other = { id: 'fan11', entity_type: 'fan', device_type: 'broadlink' }
  assert.deepEqual(getOtherDeviceCommands([current, other], current), [])
})
