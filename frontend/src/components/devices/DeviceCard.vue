<template>
  <div class="device-card" :class="{ 'disabled': isSmartIRDisabled }">
    <div class="device-header">
      <div class="device-icon" :class="styles.colorClass.value">
        <i :class="getIconClass(deviceIcon)"></i>
      </div>
      <div class="device-info">
        <h3 :title="device.name">{{ device.name }}</h3>
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
        <div class="stat" title="Learned command count">
          <i class="mdi mdi-remote"></i>
          <span>{{ commandCount }} command{{ commandCount !== 1 ? 's' : '' }}</span>
        </div>
        <div class="stat" title="HA Assigned Area">
          <i class="mdi mdi-map-marker"></i>
          <span>{{ device.area || 'No area' }}</span>
        </div>
      </div>

      <div class="device-meta">
        <span class="device-id" title="Device ID">
          <i class="mdi mdi-identifier"></i>
          {{ device.id }}
        </span>
        <span v-if="showStorageName" class="storage-name">
          <i class="mdi mdi-code-tags"></i>
          {{ device.device }}
        </span>
        <span v-if="device.broadlink_entity" class="broadlink-entity" title="Controller Device">
          <i class="mdi mdi-access-point"></i>
          {{ broadlinkFriendlyName }}
        </span>
        <span v-if="device.controller_device" class="controller-device">
          <i class="mdi mdi-access-point"></i>
          {{ getControllerName(device.controller_device) }}
        </span>
      </div>
    </div>

    <div class="device-actions">
      <button 
        @click="!isSmartIRDisabled && $emit('learn', device)" 
        class="icon-btn" 
        title="Manage Commands"
        :disabled="isSmartIRDisabled"
      >
        <i class="mdi mdi-remote-tv"></i>
      </button>
      <button 
        @click="!isSmartIRDisabled && $emit('edit', device)" 
        class="icon-btn" 
        title="Edit"
        :disabled="isSmartIRDisabled"
      >
        <i class="mdi mdi-pencil"></i>
      </button>
      <button 
        @click="!isSmartIRDisabled && $emit('delete', device)" 
        class="icon-btn danger" 
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
import { useDeviceStyles } from '@/composables/useDeviceStyles.js'
import broadlinkLogo from '@/assets/images/broadlink-logo.png'
import smartirLogo from '@/assets/images/smartir-logo.png'

const props = defineProps({
  device: {
    type: Object,
    required: true
  },
  broadlinkDevices: {
    type: Array,
    default: () => []
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
const smartirCommandCount = ref(null)

// Use centralized device styles
const styles = useDeviceStyles(computed(() => props.device.entity_type))

const deviceIcon = computed(() => {
  // Use custom icon if set, otherwise use centralized icon from styles
  if (props.device.icon) {
    return props.device.icon
  }
  return styles.icon.value
})

const getIconClass = (icon) => {
  // Convert mdi:icon-name to mdi mdi-icon-name
  if (icon && icon.startsWith('mdi:')) {
    return `mdi ${icon.replace(':', ' mdi-')}`
  }
  return `mdi mdi-${icon}`
}

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
  const device = props.broadlinkDevices.find(d => d.entity_id === entityId)
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
  
  const device = props.broadlinkDevices.find(d => d.entity_id === props.device.broadlink_entity)
  return device ? (device.name || props.device.broadlink_entity) : props.device.broadlink_entity
})

// Recursively count all command codes in a SmartIR commands structure
const countCommands = (commandsObj) => {
  if (!commandsObj || typeof commandsObj !== 'object') {
    return 0
  }
  
  let count = 0
  for (const value of Object.values(commandsObj)) {
    if (typeof value === 'string') {
      // This is an actual command code (base64 string)
      count++
    } else if (typeof value === 'object') {
      // This is a nested structure, recurse
      count += countCommands(value)
    }
  }
  
  return count
}

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
      // Count commands in the code file using recursive function
      if (code.commands) {
        smartirCommandCount.value = countCommands(code.commands)
      }
    }
  } catch (error) {
    console.error('Error fetching SmartIR command count:', error)
  }
}

onMounted(async () => {
  // Fetch SmartIR command count if this is a SmartIR device
  const deviceType = props.device.device_type || 'broadlink'
  if (deviceType === 'smartir') {
    await fetchSmartIRCommandCount()
  }
})
</script>

<style scoped>
@import '@/assets/css/variables.css';
@import '@/assets/css/card-styles.css';

/* Card base styles imported from card-styles.css */

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

/* Header, icon, info, labels, and tags imported from card-styles.css */

.device-info h3 {
  padding-right: 36px;
}

/* Tag backgrounds imported from card-styles.css */

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

/* Body, stats, meta, actions, and buttons imported from card-styles.css */
</style>
