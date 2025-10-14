<template>
  <div class="device-card">
    <div class="device-header">
      <div class="device-icon">
        <i :class="`mdi mdi-${deviceIcon}`"></i>
      </div>
      <div class="device-info">
        <h3>{{ device.name }}</h3>
        <span class="device-type">{{ deviceTypeLabel }}</span>
      </div>
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
      </div>
    </div>

    <div class="device-actions">
      <button @click="$emit('learn', device)" class="action-btn primary" title="Manage Commands">
        <i class="mdi mdi-remote-tv"></i>
        <span>Commands</span>
      </button>
      <button @click="$emit('edit', device)" class="action-btn" title="Edit">
        <i class="mdi mdi-pencil"></i>
      </button>
      <button @click="$emit('delete', device)" class="action-btn danger" title="Delete">
        <i class="mdi mdi-delete"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import api from '@/services/api'

const props = defineProps({
  device: {
    type: Object,
    required: true
  }
})

defineEmits(['edit', 'delete', 'learn'])

const broadlinkDevices = ref([])

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

const commandCount = computed(() => {
  return Object.keys(props.device.commands || {}).length
})

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

onMounted(async () => {
  try {
    const response = await api.get('/api/broadlink/devices')
    broadlinkDevices.value = response.data.devices || []
  } catch (error) {
    console.error('Error loading Broadlink devices:', error)
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
}

.device-card:hover {
  box-shadow: var(--ha-shadow-md);
  border-color: var(--ha-primary-color);
}

.device-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.device-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.device-icon i {
  font-size: 28px;
  color: var(--ha-primary-color);
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-info h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
.storage-name,
.broadlink-entity {
  font-size: 12px;
  color: var(--ha-text-secondary-color);
  font-family: monospace;
  display: flex;
  align-items: center;
  gap: 4px;
}

.device-id i,
.storage-name i,
.broadlink-entity i {
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
  background: var(--ha-hover-color);
  border-color: var(--ha-primary-color);
}

.action-btn.primary {
  background: var(--ha-primary-color);
  color: white;
  border-color: var(--ha-primary-color);
}

.action-btn.primary:hover {
  opacity: 0.9;
}

.action-btn.danger:hover {
  background: rgba(var(--ha-error-rgb), 0.1);
  border-color: var(--ha-error-color);
  color: var(--ha-error-color);
}

.action-btn i {
  font-size: 18px;
}
</style>
