/**
 * Framework-free unit tests for SmartIR JSON profile generator.
 *
 * Run with: npm test
 * (or: node test/jsonGenerator.test.mjs)
 */

import { strict as assert } from 'node:assert'
import { test } from 'node:test'
import { generateSmartIRJson } from '../src/components/smartir/jsonGenerator.js'

const CLIMATE_PROFILE = {
  platform: 'climate',
  manufacturer: 'Acme',
  model: 'AC-100',
  broadlinkDevice: 'remote.broadlink_rm4_pro',
  commandType: 'ir',
  config: {
    temperatureUnit: 'C',
    minTemp: 16,
    maxTemp: 30,
    precision: 1,
    modes: ['off', 'cool', 'heat'],
    fanModes: ['auto', 'low', 'high'],
    swingModes: [],
    presetModes: [],
  },
  commands: {
    off: 'JgBQAAA=',
    cool_24_auto: 'JgBQAA1=',
    heat_22_low: 'JgBQAA2=',
  },
}

test('climate profile includes temperatureUnit (litinoveweedle fork requirement)', () => {
  const json = generateSmartIRJson(CLIMATE_PROFILE)
  assert.equal(json.temperatureUnit, 'C')
})

test('climate profile temperatureUnit defaults to C when not set', () => {
  const profile = {
    ...CLIMATE_PROFILE,
    config: { ...CLIMATE_PROFILE.config, temperatureUnit: undefined },
  }
  const json = generateSmartIRJson(profile)
  assert.equal(json.temperatureUnit, 'C')
})

test('climate profile preserves Fahrenheit temperatureUnit', () => {
  const profile = {
    ...CLIMATE_PROFILE,
    config: { ...CLIMATE_PROFILE.config, temperatureUnit: 'F' },
  }
  const json = generateSmartIRJson(profile)
  assert.equal(json.temperatureUnit, 'F')
})

test('climate profile includes all required SmartIR fields', () => {
  const json = generateSmartIRJson(CLIMATE_PROFILE)
  assert.equal(json.manufacturer, 'Acme')
  assert.deepEqual(json.supportedModels, ['AC-100'])
  assert.equal(json.supportedController, 'Broadlink')
  assert.equal(json.commandsEncoding, 'Base64')
  assert.equal(json.commandType, 'ir')
  assert.equal(json.minTemperature, 16)
  assert.equal(json.maxTemperature, 30)
  assert.equal(json.precision, 1)
  assert.deepEqual(json.operationModes, ['cool', 'heat']) // 'off' excluded
  assert.deepEqual(json.fanModes, ['auto', 'low', 'high'])
})

test('climate profile nests flat commands correctly', () => {
  const json = generateSmartIRJson(CLIMATE_PROFILE)
  assert.equal(json.commands.off, 'JgBQAAA=')
  assert.equal(json.commands.cool.auto['24'], 'JgBQAA1=')
  assert.equal(json.commands.heat.low['22'], 'JgBQAA2=')
})

test('non-climate platforms do not include temperatureUnit', () => {
  for (const platform of ['fan', 'media_player', 'light']) {
    const json = generateSmartIRJson({
      platform,
      manufacturer: 'Acme',
      model: 'X',
      commandType: 'ir',
      config: { temperatureUnit: 'C' },
      commands: { turn_on: 'JgBQAAA=' },
    })
    assert.ok(!('temperatureUnit' in json), `${platform} should not have temperatureUnit`)
  }
})

test('fan profile maps UI commands to SmartIR nested structure', () => {
  const json = generateSmartIRJson({
    platform: 'fan',
    manufacturer: 'Acme',
    model: 'Fan-1',
    commandType: 'ir',
    config: {},
    commands: {
      turn_on: 'JgOn==',
      turn_off: 'JgOff==',
      speed_1: 'JgLo==',
      speed_2: 'JgMd==',
      speed_3: 'JgHi==',
    },
  })
  assert.equal(json.commands.on, 'JgOn==')
  assert.equal(json.commands.off, 'JgOff==')
  assert.equal(json.commands.default.low, 'JgLo==')
  assert.equal(json.commands.default.medium, 'JgMd==')
  assert.equal(json.commands.default.high, 'JgHi==')
})
