<template>
  <div class="device-card" :class="{ 'disabled': isSmartIRDisabled }">
    <div class="device-header">
      <div class="device-icon">
        <i :class="`mdi mdi-${deviceIcon}`"></i>
      </div>
      <div class="device-info">
        <h3>{{ device.name }}</h3>
        <div class="device-labels">
          <span class="device-type">{{ deviceTypeLabel }}</span>
        </div>
      </div>
      <img 
        :src="deviceSourceLogo" 
        :alt="deviceSourceLabel"
        :title="deviceSourceLabel"
        class="device-source-logo"
      />
    </div>

    <div class="device-body">
      <div class="device-stats">
        <div class="stat">
          <i class="mdi mdi-remote"></i>
          <span>{{ commandCount }} commands</span>
        </div>
        <div class="stat">
          <i class="mdi mdi-map-marker"></i>
          <span>{{ device.area || 'No area' }}</span>
        </div>
      </div>

      <div class="device-meta">
        <span class="device-id">
          <i class="mdi mdi-identifier"></i>
          {{ device.id }}
        </span>
        <span v-if="showStorageName" class="storage-name">
          <i class="mdi mdi-code-tags"></i>
          {{ device.device }}
        </span>
        <span v-if="device.broadlink_entity" class="broadlink-entity">
          <i class="mdi mdi-access-point"></i>
          {{ broadlinkFriendlyName }}
        </span>
        <span v-if="device.controller_device" class="controller-device">
          <i class="mdi mdi-access-point"></i>
          Controller: {{ getControllerName(device.controller_device) }}
        </span>
      </div>
    </div>

    <div class="device-actions">
      <button 
        @click="!isSmartIRDisabled && $emit('learn', device)" 
        class="action-btn" 
        title="Manage Commands"
        :disabled="isSmartIRDisabled"
      >
        <i class="mdi mdi-remote-tv"></i>
        <span>Commands</span>
      </button>
      <button 
        @click="!isSmartIRDisabled && $emit('edit', device)" 
        class="action-btn" 
        title="Edit"
        :disabled="isSmartIRDisabled"
      >
        <i class="mdi mdi-pencil"></i>
      </button>
      <button 
        @click="!isSmartIRDisabled && $emit('delete', device)" 
        class="action-btn danger" 
        title="Delete"
        :disabled="isSmartIRDisabled"
      >
        <i class="mdi mdi-delete"></i>
      </button>
    </div>
    
    <!-- SmartIR Disabled Overlay -->
    <div v-if="isSmartIRDisabled" class="disabled-overlay">
      <div class="disabled-message">
        <i class="mdi mdi-eye-off"></i>
        <span>SmartIR Not Installed</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import api from '@/services/api'
import broadlinkLogo from '@/assets/images/broadlink-logo.png'
import smartirLogo from '@/assets/images/smartir-logo.png'

const props = defineProps({
  device: {
    type: Object,
    required: true
  }
})

// Check if SmartIR simulation mode is active
const isSmartIRSimulating = computed(() => {
  return localStorage.getItem('smartir_simulate_not_installed') === 'true'
})

// Check if this is a SmartIR device and simulation is active
const isSmartIRDisabled = computed(() => {
  return props.device.device_type === 'smartir' && isSmartIRSimulating.value
})

defineEmits(['edit', 'delete', 'learn'])

const broadlinkDevices = ref([])
const smartirCommandCount = ref(null)

const deviceIcon = computed(() => {
  // Use custom icon if set, otherwise use default based on entity type
  if (props.device.icon) {
    // Remove 'mdi:' prefix if present
    return props.device.icon.replace('mdi:', '')
  }
  
  const icons = {
    light: 'lightbulb',
    fan: 'fan',
    switch: 'light-switch',
    media_player: 'television',
    cover: 'window-shutter'
  }
  return icons[props.device.entity_type] || 'devices'
})

const deviceTypeLabel = computed(() => {
  const labels = {
    light: 'Light',
    fan: 'Fan',
    switch: 'Switch',
    media_player: 'Media Player',
    cover: 'Cover'
  }
  return labels[props.device.entity_type] || props.device.entity_type
})

const deviceSourceLabel = computed(() => {
  const deviceType = props.device.device_type || 'broadlink'
  return deviceType === 'smartir' ? 'SmartIR' : 'Broadlink'
})

const deviceSourceLogo = computed(() => {
  const deviceType = props.device.device_type || 'broadlink'
  return deviceType === 'smartir' ? smartirLogo : broadlinkLogo
})

const commandCount = computed(() => {
  const deviceType = props.device.device_type || 'broadlink'
  
  if (deviceType === 'smartir') {
    // For SmartIR devices, show the command count from the code file
    return smartirCommandCount.value !== null ? smartirCommandCount.value : 0
  }
  
  // For Broadlink devices, show learned commands
  return Object.keys(props.device.commands || {}).length
})

const getControllerName = (entityId) => {
  if (!entityId) return ''
  const device = broadlinkDevices.value.find(d => d.entity_id === entityId)
  return device ? (device.name || entityId) : entityId
}

const showStorageName = computed(() => {
  if (!props.device.device) return false
  
  // Extract the name part from entity_id (e.g., "light.kitchen_floor" -> "kitchen_floor")
  const entityName = props.device.id.includes('.') 
    ? props.device.id.split('.')[1] 
    : props.device.id
  
  // Only show storage name if it's different from the entity name
  return props.device.device !== entityName
})

const broadlinkFriendlyName = computed(() => {
  if (!props.device.broadlink_entity) return ''
  
  const device = broadlinkDevices.value.find(d => d.entity_id === props.device.broadlink_entity)
  return device ? (device.name || props.device.broadlink_entity) : props.device.broadlink_entity
})

const fetchSmartIRCommandCount = async () => {
  if (!props.device.device_code || !props.device.entity_type) return
  
  try {
    const response = await api.get('/api/smartir/codes/code', {
      params: {
        entity_type: props.device.entity_type,
        code_id: props.device.device_code
      }
    })
    
    if (response.data.success && response.data.code) {
      const code = response.data.code
      // Count commands in the code file
      if (code.commands) {
        smartirCommandCount.value = Object.keys(code.commands).length
      }
    }
  } catch (error) {
    console.error('Error fetching SmartIR command count:', error)
  }
}

onMounted(async () => {
  try {
    const response = await api.get('/api/broadlink/devices')
    broadlinkDevices.value = response.data.devices || []
  } catch (error) {
    console.error('Error loading Broadlink devices:', error)
  }
  
  // Fetch SmartIR command count if this is a SmartIR device
  const deviceType = props.device.device_type || 'broadlink'
  if (deviceType === 'smartir') {
    await fetchSmartIRCommandCount()
  }
})
</script>

<style scoped>
.device-card {
  background: var(--ha-card-background);
  border-radius: 12px;
  border: 1px solid var(--ha-border-color);
  padding: 20px;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

.device-card:hover {
  box-shadow: var(--ha-shadow-md);
  border-color: var(--ha-primary-color);
}

.device-card.disabled {
  pointer-events: none;
  filter: grayscale(40%);
}

.device-card.disabled:hover {
  box-shadow: none;
  border-color: var(--ha-border-color);
}

.disabled-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(var(--ha-card-background-rgb, 255, 255, 255), 0.75);
  backdrop-filter: blur(1px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  z-index: 10;
  pointer-events: all;
}

.disabled-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  text-align: center;
}

.disabled-message i {
  font-size: 48px;
  color: var(--ha-warning-color, #ff9800);
  opacity: 0.7;
}

.disabled-message span {
  font-size: 14px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
}

.device-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  position: relative;
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.device-icon i {
  font-size: 24px;
  color: var(--ha-primary-color);
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  white-space: normal;
  line-height: 1.3;
  max-height: 2.6em;
  padding-right: 36px;
}

.device-labels {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.device-type {
  display: inline-block;
  padding: 2px 8px;
  background: var(--ha-surface-color);
  border-radius: 4px;
  font-size: 12px;
  color: var(--ha-text-secondary-color);
  font-weight: 500;
}

.device-source-logo {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 28px;
  height: 28px;
  object-fit: contain;
  opacity: 0.8;
  transition: all 0.2s;
  cursor: help;
}

.device-source-logo:hover {
  opacity: 1;
  transform: scale(1.1);
}

.device-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-stats {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ha-text-secondary-color);
  font-size: 14px;
}

.stat i {
  font-size: 16px;
}

.device-meta {
  padding-top: 8px;
  border-top: 1px solid var(--ha-border-color);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.device-id,
.device-code,
.storage-name,
.broadlink-entity,
.controller-device {
  font-size: 12px;
  color: var(--ha-text-secondary-color);
  font-family: monospace;
  display: flex;
  align-items: center;
  gap: 4px;
}

.device-id i,
.device-code i,
.storage-name i,
.broadlink-entity i,
.controller-device i {
  font-size: 14px;
  flex-shrink: 0;
}

.device-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--ha-border-color);
}

.action-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid var(--ha-border-color);
  background: var(--ha-card-background);
  color: var(--ha-text-primary-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
}

.action-btn:hover {
  background: var(--ha-primary-color);
  color: white;
  border-color: var(--ha-primary-color);
}

.action-btn.danger:hover {
  background: var(--ha-error-color, #f44336);
  color: white;
  border-color: var(--ha-error-color, #f44336);
}

.action-btn i {
  font-size: 18px;
}
</style>
