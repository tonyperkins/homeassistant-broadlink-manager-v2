<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ isEdit ? 'Edit Device' : 'Add New Device' }}</h2>
        <button @click="$emit('cancel')" class="close-btn">
          <i class="mdi mdi-close"></i>
        </button>
      </div>

      <form id="device-form" @submit.prevent="handleSubmit" class="modal-body">
        <div class="form-group" :class="{ 'has-error': validationErrors.name }">
          <label for="device-name">Device Name *</label>
          <div class="input-wrapper">
            <input
              id="device-name"
              ref="nameInput"
              v-model="formData.name"
              type="text"
              placeholder="e.g., Living Room TV"
              @input="clearValidationError('name')"
            />
            <div v-if="validationErrors.name" class="validation-tooltip">
              <i class="mdi mdi-alert"></i>
              {{ validationErrors.name }}
            </div>
          </div>
          <small>Friendly name for this device</small>
        </div>

        <div class="form-group" :class="{ 'has-error': validationErrors.entity_type }">
          <label for="entity-type">Entity Type *</label>
          <div class="input-wrapper">
            <select 
              id="entity-type" 
              ref="typeSelect"
              v-model="formData.entity_type"
              @change="clearValidationError('entity_type')"
            >
            <option value="">-- Select Type --</option>
            <option value="light">💡 Light</option>
            <option value="fan">🌀 Fan</option>
            <option value="switch">🔌 Switch</option>
            <option value="media_player">📺 Media Player</option>
            <option value="cover">🪟 Cover (Blinds/Curtains)</option>
            <option value="climate" :disabled="!smartirInstalled">
              🌡️ Climate {{ smartirInstalled ? '' : '(Requires SmartIR)' }}
            </option>
            </select>
            <div v-if="validationErrors.entity_type" class="validation-tooltip">
              <i class="mdi mdi-alert"></i>
              {{ validationErrors.entity_type }}
            </div>
          </div>
          
          <!-- SmartIR Info/Warning -->
          <div v-if="formData.entity_type === 'climate'" class="smartir-notice">
            <div v-if="smartirInstalled" class="notice-success">
              <i class="mdi mdi-check-circle"></i>
              <span>SmartIR detected! Climate entities will be created via SmartIR profiles.</span>
            </div>
            <div v-else class="notice-warning">
              <i class="mdi mdi-alert"></i>
              <div>
                <strong>SmartIR Required</strong>
                <p>Climate entities (AC, heaters) require SmartIR integration.</p>
                <a href="https://github.com/smartHomeHub/SmartIR" target="_blank" class="smartir-link">
                  Install SmartIR →
                </a>
              </div>
            </div>
          </div>
          
          <!-- SmartIR Optional Notice for other supported types -->
          <div v-else-if="smartirInstalled && ['media_player', 'fan', 'light'].includes(formData.entity_type)" class="smartir-notice">
            <div class="notice-info">
              <i class="mdi mdi-information"></i>
              <span>💡 SmartIR available! You can use pre-configured codes or learn your own.</span>
            </div>
          </div>
          
          <small v-else-if="!smartirInstalled && formData.entity_type">
            💡 Tip: Install <a href="https://github.com/smartHomeHub/SmartIR" target="_blank" class="inline-link">SmartIR</a> for pre-configured {{ formData.entity_type === 'climate' ? 'climate' : formData.entity_type }} device codes
          </small>
        </div>

        <!-- Device Type Selection -->
        <div class="form-group">
          <label for="device-type">Device Type *</label>
          <select
            id="device-type"
            v-model="formData.device_type"
            required
            :disabled="isEdit"
          >
            <option value="">-- Select Device Type --</option>
            <option value="broadlink">📡 Broadlink Device (Learn IR Codes)</option>
            <option v-if="smartirEnabled" value="smartir" :disabled="!smartirInstalled || !isSmartIRSupported">
              🌐 SmartIR Device {{ getSmartIROptionLabel }}
            </option>
          </select>
          <small v-if="isEdit">Cannot change device type after creation</small>
          <small v-else-if="formData.device_type === 'smartir'">Using pre-configured codes from SmartIR repository</small>
          <small v-else-if="formData.device_type === 'broadlink'">Learn and store your own IR codes</small>
          <small v-else>Choose how to configure this device</small>
        </div>

        <!-- Area field removed from creation - will be set in HA after entity generation -->
        <div v-if="isEdit" class="form-group">
          <label for="device-area">Area</label>
          <div class="area-display-readonly">
            <input 
              id="device-area" 
              :value="formData.area || 'Not assigned'" 
              type="text" 
              readonly
              class="readonly-input"
            />
            <button 
              type="button"
              @click="syncArea" 
              :disabled="syncingArea"
              class="sync-area-btn"
              title="Sync area from Home Assistant"
            >
              <i :class="syncingArea ? 'mdi mdi-loading mdi-spin' : 'mdi mdi-refresh'"></i>
            </button>
          </div>
          <small>
            <i class="mdi mdi-information-outline"></i>
            Set area in Home Assistant, then click sync. 
            <a :href="getEntityUrl()" target="_blank" class="inline-link">Open in HA →</a>
          </small>
        </div>
        <div v-else class="form-group">
          <div class="info-notice">
            <i class="mdi mdi-information-outline"></i>
            <span><strong>Area Assignment:</strong> After generating entities and restarting Home Assistant, you can assign areas in HA and sync them here.</span>
          </div>
        </div>

        <div class="form-group">
          <label for="device-icon">Icon</label>
          <IconPicker
            v-model="formData.icon"
            inputId="device-icon"
            placeholder="e.g., mdi:television"
          />
          <small>Optional: Material Design Icon name</small>
        </div>

        <!-- Remote Device Selection (for Broadlink type) -->
        <div v-if="formData.device_type === 'broadlink'" class="form-group" :class="{ 'has-error': validationErrors.broadlink_entity }">
          <label for="broadlink-entity">Remote Device *</label>
          <div class="input-wrapper">
            <select 
              v-if="!isEdit || !hasCommands"
              id="broadlink-entity"
              ref="broadlinkSelect"
              v-model="formData.broadlink_entity"
              @change="clearValidationError('broadlink_entity')"
            >
              <option value="">-- Select Remote Device --</option>
              <option 
                v-for="device in broadlinkDevices" 
                :key="device.entity_id" 
                :value="device.entity_id"
              >
                {{ device.name || device.entity_id }}
                <template v-if="device.area_name"> - {{ device.area_name }}</template>
              </option>
            </select>
            <input
              v-else
              id="broadlink-entity"
              :value="broadlinkFriendlyName"
              type="text"
              readonly
              disabled
            />
            <div v-if="validationErrors.broadlink_entity" class="validation-tooltip">
              <i class="mdi mdi-alert"></i>
              {{ validationErrors.broadlink_entity }}
            </div>
          </div>
          <small v-if="!isEdit || !hasCommands">Required: Select which remote device to use for sending commands</small>
          <small v-else>Cannot change remote device after commands are learned</small>
        </div>

        <!-- SmartIR Device Configuration (for SmartIR type) -->
        <div v-if="formData.device_type === 'smartir'" class="smartir-section">
          <div class="section-header">
            <i class="mdi mdi-cloud-download"></i>
            <span>SmartIR Device Configuration</span>
          </div>
          <SmartIRDeviceSelector
            ref="smartirSelector"
            :entity-type="formData.entity_type"
            v-model="smartirData"
            :broadlink-devices="broadlinkDevices"
            @change="handleSmartIRChange"
          />
        </div>
      </form>

      <div class="modal-footer">
        <button type="button" @click="$emit('cancel')" class="btn btn-secondary">
          Cancel
        </button>
        <button type="submit" form="device-form" class="btn btn-primary">
          <i class="mdi mdi-check"></i>
          {{ isEdit ? 'Update' : 'Create' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, watch } from 'vue'
import api from '@/services/api'
import IconPicker from '../common/IconPicker.vue'
import SmartIRDeviceSelector from './SmartIRDeviceSelector.vue'

const props = defineProps({
  device: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['save', 'cancel'])

// Inject SmartIR status and enabled state
const smartirStatus = inject('smartirStatus')
const smartirEnabled = inject('smartirEnabled')
const smartirInstalled = computed(() => {
  // Check if simulating not-installed
  const isSimulating = localStorage.getItem('smartir_simulate_not_installed') === 'true'
  if (isSimulating) return false
  return smartirStatus?.value?.installed || false
})

const isEdit = computed(() => !!props.device)

// Check if current entity type supports SmartIR
const isSmartIRSupported = computed(() => {
  const supportedTypes = ['climate', 'media_player', 'fan', 'light']
  return supportedTypes.includes(formData.value.entity_type)
})

// Get SmartIR option label based on installation and entity type support
const getSmartIROptionLabel = computed(() => {
  if (!smartirInstalled.value) {
    return '(Requires SmartIR)'
  }
  if (!isSmartIRSupported.value && formData.value.entity_type) {
    return '(Not supported for this type)'
  }
  return '(Pre-configured Codes)'
})

const hasCommands = computed(() => {
  const commands = props.device?.commands || {}
  return Object.keys(commands).length > 0
})

const broadlinkFriendlyName = computed(() => {
  if (!formData.value.broadlink_entity) return ''
  
  const device = broadlinkDevices.value.find(d => d.entity_id === formData.value.broadlink_entity)
  return device ? (device.name || formData.value.broadlink_entity) : formData.value.broadlink_entity
})

const formData = ref({
  name: '',
  entity_type: '',
  device_type: 'broadlink', // Default to broadlink
  device: '', // Storage name for Broadlink devices
  area: '',
  icon: '',
  broadlink_entity: '',
  enabled: true,
  commands: {}
})

const validationErrors = ref({
  name: '',
  entity_type: '',
  broadlink_entity: ''
})

const smartirData = ref({})
const smartirSelector = ref(null)

const areas = ref([])
const broadlinkDevices = ref([])
const nameInput = ref(null)
const typeSelect = ref(null)
const broadlinkSelect = ref(null)
const iconAutoSet = ref(false) // Track if icon was auto-set vs manually set

onMounted(async () => {
  if (props.device) {
    formData.value = { 
      ...props.device,
      // Ensure device_type is set (default to 'broadlink' for backward compatibility)
      device_type: props.device.device_type || 'broadlink'
    }
    
    // If editing a SmartIR device, populate smartirData
    if (formData.value.device_type === 'smartir') {
      smartirData.value = {
        manufacturer: props.device.manufacturer,
        model: props.device.model,
        device_code: props.device.device_code,
        controller_device: props.device.controller_device,
        temperature_sensor: props.device.temperature_sensor,
        humidity_sensor: props.device.humidity_sensor
      }
    }
  }
  await Promise.all([loadAreas(), loadBroadlinkDevices()])
})

const loadAreas = async () => {
  try {
    const response = await api.get('/api/areas')
    areas.value = response.data.areas || []
  } catch (error) {
    console.error('Error loading areas:', error)
    areas.value = []
  }
}

const loadBroadlinkDevices = async () => {
  try {
    // Use new endpoint that returns all remote devices (Broadlink, Xiaomi, etc.)
    const response = await api.get('/api/remote/devices')
    // The response is wrapped in a 'devices' property
    const devices = response.data.devices || []
    broadlinkDevices.value = devices
    console.log('Loaded remote devices:', devices)
  } catch (error) {
    console.error('Error loading remote devices:', error)
    broadlinkDevices.value = []
  }
}

// Smart area detection from device name
const detectAreaFromName = (name) => {
  if (!name) return ''
  
  const lowerName = name.toLowerCase()
  
  // Check each area to see if it's mentioned in the name
  for (const area of areas.value) {
    const lowerArea = area.toLowerCase()
    if (lowerName.includes(lowerArea)) {
      return area
    }
  }
  
  return ''
}

// Smart icon selection based on entity type and name
const getDefaultIcon = (entityType, name = '') => {
  const lowerName = name.toLowerCase()
  
  // Name-based detection (more specific)
  if (lowerName.includes('tv')) return 'mdi:television'
  if (lowerName.includes('lamp')) return 'mdi:lamp'
  if (lowerName.includes('ceiling')) return 'mdi:ceiling-light'
  if (lowerName.includes('floor')) return 'mdi:floor-lamp'
  if (lowerName.includes('desk')) return 'mdi:desk-lamp'
  if (lowerName.includes('fan')) return 'mdi:fan'
  if (lowerName.includes('ac') || lowerName.includes('air con')) return 'mdi:air-conditioner'
  if (lowerName.includes('heater')) return 'mdi:radiator'
  if (lowerName.includes('blind')) return 'mdi:blinds'
  if (lowerName.includes('curtain')) return 'mdi:curtains'
  if (lowerName.includes('garage')) return 'mdi:garage'
  if (lowerName.includes('speaker') || lowerName.includes('stereo')) return 'mdi:speaker'
  if (lowerName.includes('receiver')) return 'mdi:audio-video'
  
  // Entity type defaults
  const typeIcons = {
    light: 'mdi:lightbulb',
    fan: 'mdi:fan',
    switch: 'mdi:light-switch',
    media_player: 'mdi:television',
    cover: 'mdi:window-shutter',
    climate: 'mdi:thermostat'
  }
  
  return typeIcons[entityType] || 'mdi:devices'
}

// Watch device name for smart area detection
watch(() => formData.value.name, (newName) => {
  // Only auto-detect if user hasn't manually selected an area yet
  if (!isEdit.value && newName && !formData.value.area) {
    const detectedArea = detectAreaFromName(newName)
    if (detectedArea) {
      formData.value.area = detectedArea
    }
  }
  
  // Auto-update icon if it was auto-set or empty
  if (!isEdit.value && newName && formData.value.entity_type && (iconAutoSet.value || !formData.value.icon)) {
    formData.value.icon = getDefaultIcon(formData.value.entity_type, newName)
    iconAutoSet.value = true
  }
})

// Watch entity type for smart icon selection
watch(() => formData.value.entity_type, (newType) => {
  // Auto-update icon if it was auto-set or empty
  if (!isEdit.value && newType && (iconAutoSet.value || !formData.value.icon)) {
    formData.value.icon = getDefaultIcon(newType, formData.value.name)
    iconAutoSet.value = true
  }
})

// Watch icon field to detect manual changes
watch(() => formData.value.icon, (newIcon, oldIcon) => {
  // If user manually changes the icon (not from our auto-set), mark it as manual
  if (oldIcon !== undefined && newIcon !== oldIcon && !iconAutoSet.value) {
    iconAutoSet.value = false
  }
  // If user clears the icon, allow auto-set again
  if (!newIcon) {
    iconAutoSet.value = false
  }
})

const syncingArea = ref(false)

const syncArea = async () => {
  if (!props.device?.id) return
  
  syncingArea.value = true
  try {
    const response = await api.post(`/api/devices/${props.device.id}/sync-area`)
    
    if (response.data.success) {
      formData.value.area = response.data.area || ''
      
      if (response.data.area) {
        // Success notification
        console.log(`Area synced: ${response.data.area}`)
      } else {
        // Info notification
        console.log('No area assigned in Home Assistant')
      }
    } else {
      // Warning notification
      console.warn(response.data.message || 'Entity not found in HA')
    }
  } catch (error) {
    console.error('Failed to sync area:', error)
  } finally {
    syncingArea.value = false
  }
}

const getEntityUrl = () => {
  if (!props.device?.id || !formData.value.entity_type) return '#'
  
  const entityType = formData.value.entity_type
  const entityId = `${entityType}.${props.device.id}`
  
  // Use relative path that works in both direct and ingress modes
  return `/config/entities/entity/${entityId}`
}

const validateForm = () => {
  // Clear all errors first
  validationErrors.value = {
    name: '',
    entity_type: '',
    broadlink_entity: ''
  }
  
  let isValid = true
  
  // Validate name
  if (!formData.value.name || formData.value.name.trim() === '') {
    validationErrors.value.name = 'Device name is required'
    isValid = false
  }
  
  // Validate entity type
  if (!formData.value.entity_type) {
    validationErrors.value.entity_type = 'Entity type is required'
    isValid = false
  }
  
  // Validate broadlink entity (only for broadlink device type)
  if (formData.value.device_type === 'broadlink' && !formData.value.broadlink_entity) {
    validationErrors.value.broadlink_entity = 'Broadlink device is required'
    isValid = false
  }
  
  return isValid
}

const clearValidationError = (field) => {
  validationErrors.value[field] = ''
}

const handleSubmit = async () => {
  // Validate SmartIR fields if SmartIR device
  if (formData.value.device_type === 'smartir') {
    if (smartirSelector.value && !smartirSelector.value.validate()) {
      return
    }
    
    // Create SmartIR config object
    const submitData = {
      ...formData.value,
      smartir_config: {
        manufacturer: smartirData.value.manufacturer,
        model: smartirData.value.model,
        code_id: smartirData.value.device_code,
        controller_device: smartirData.value.controller_device
      }
    }
    
    emit('save', submitData)
  } else {
    // Validate Broadlink form
    if (!validateForm()) {
      return
    }
    emit('save', { ...formData.value })
  }
}

const handleSmartIRChange = (data) => {
  smartirData.value = data
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: var(--ha-card-background);
  border-radius: 12px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--ha-shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--ha-border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--ha-text-secondary-color);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--ha-hover-color);
  color: var(--ha-text-primary-color);
}

.close-btn i {
  font-size: 24px;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
}

.form-group small {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--ha-text-secondary-color);
}

.error-message {
  color: var(--ha-error-color, #f44336) !important;
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.error-message i {
  font-size: 14px;
}

.hint-message {
  color: var(--ha-text-secondary-color);
  font-style: italic;
}

.input-error {
  border-color: var(--ha-error-color, #f44336) !important;
  background: rgba(244, 67, 54, 0.05);
}

.inline-link {
  color: var(--ha-primary-color);
  text-decoration: none;
  font-weight: 500;
}

.inline-link:hover {
  text-decoration: underline;
}

.smartir-notice {
  margin-top: 8px;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
}

.notice-success {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
  color: #4caf50;
  display: flex;
  align-items: center;
  gap: 8px;
}

.notice-success i {
  font-size: 20px;
}

.notice-warning {
  background: rgba(255, 152, 0, 0.1);
  border: 1px solid rgba(255, 152, 0, 0.3);
  color: #f57c00;
  display: flex;
  gap: 8px;
}

.notice-warning i {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.notice-warning strong {
  display: block;
  margin-bottom: 4px;
}

.notice-warning p {
  margin: 0 0 8px 0;
  font-size: 12px;
  opacity: 0.9;
}

.notice-info {
  background: rgba(3, 169, 244, 0.1);
  border: 1px solid rgba(3, 169, 244, 0.3);
  color: #03a9f4;
  display: flex;
  align-items: center;
  gap: 8px;
}

.notice-info i {
  font-size: 20px;
}

.smartir-link {
  color: var(--ha-primary-color);
  text-decoration: none;
  font-weight: 600;
  font-size: 12px;
}

.smartir-link:hover {
  text-decoration: underline;
}

/* Area Display (Read-only) */
.area-display-readonly {
  display: flex;
  gap: 8px;
  align-items: center;
}

.readonly-input {
  flex: 1;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-divider-color, #e0e0e0);
  color: var(--ha-primary-text-color);
  opacity: 0.7;
  cursor: not-allowed;
}

.sync-area-btn {
  padding: 8px 12px;
  background: var(--ha-primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  min-width: 40px;
}

.sync-area-btn:hover:not(:disabled) {
  background: var(--ha-primary-color-dark, #0288d1);
  transform: scale(1.05);
}

.sync-area-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sync-area-btn i {
  font-size: 18px;
}

.info-notice {
  background: rgba(3, 169, 244, 0.1);
  border: 1px solid rgba(3, 169, 244, 0.3);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: var(--ha-primary-text-color);
}

.info-notice i {
  color: #03a9f4;
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-notice span {
  font-size: 13px;
  line-height: 1.5;
}

.inline-link {
  color: var(--ha-primary-color);
  text-decoration: none;
  font-weight: 500;
}

.inline-link:hover {
  text-decoration: underline;
}

/* SmartIR Section */
.smartir-section {
  background: var(--ha-card-background);
  border: 1px solid var(--ha-divider-color, #e0e0e0);
  border-radius: 8px;
  padding: 20px;
  margin-top: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-weight: 600;
  font-size: 16px;
  color: var(--ha-primary-color, #03a9f4);
  padding-bottom: 12px;
  border-bottom: 2px solid var(--ha-divider-color, #e0e0e0);
}

.section-header i {
  font-size: 24px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 24px;
  border-top: 1px solid var(--ha-border-color);
  background: var(--ha-card-background);
  flex-shrink: 0;
}

/* Validation tooltip styling */
.input-wrapper {
  position: relative;
}

.form-group.has-error input,
.form-group.has-error select {
  border-color: #ff9800;
}

.validation-tooltip {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  padding: 10px 14px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 8px;
  color: #333;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  z-index: 1000;
  animation: tooltipFadeIn 0.2s ease-out;
}

.validation-tooltip::before {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 16px;
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid white;
  filter: drop-shadow(0 -1px 1px rgba(0, 0, 0, 0.1));
}

.validation-tooltip i {
  font-size: 18px;
  color: #ff9800;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: 0;
  }
  
  .modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
}
</style>
