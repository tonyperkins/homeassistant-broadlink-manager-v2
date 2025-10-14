<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ isEdit ? 'Edit Device' : 'Add New Device' }}</h2>
        <button @click="$emit('cancel')" class="close-btn">
          <i class="mdi mdi-close"></i>
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-body">
        <div class="form-group">
          <label for="device-name">Device Name *</label>
          <input
            id="device-name"
            ref="nameInput"
            v-model="formData.name"
            type="text"
            placeholder="e.g., Living Room TV"
            required
            @input="clearValidation('nameInput')"
          />
        </div>

        <div class="form-group">
          <label for="entity-type">Entity Type *</label>
          <select 
            id="entity-type" 
            ref="typeSelect"
            v-model="formData.entity_type"
            required
            @change="clearValidation('typeSelect')"
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
          
          <small v-else-if="!smartirInstalled">
            💡 Tip: Install <a href="https://github.com/smartHomeHub/SmartIR" target="_blank" class="inline-link">SmartIR</a> for climate device support
          </small>
        </div>

        <div class="form-group">
          <label for="device-area">Area</label>
          <select id="device-area" v-model="formData.area">
            <option value="">-- No Area --</option>
            <option v-for="area in areas" :key="area" :value="area">
              {{ area }}
            </option>
          </select>
          <small>Optional: Assign to a Home Assistant area</small>
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

        <div class="form-group">
          <label for="broadlink-entity">Broadlink Device</label>
          <select 
            v-if="!isEdit || !hasCommands"
            id="broadlink-entity"
            ref="broadlinkSelect"
            v-model="formData.broadlink_entity"
            required
            @change="clearValidation('broadlinkSelect')"
          >
            <option value="">-- Select Broadlink Device --</option>
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
          <small v-if="!isEdit || !hasCommands">Required: Select which Broadlink device to use</small>
          <small v-else>Cannot change Broadlink device after commands are learned</small>
        </div>

        <div class="modal-footer">
          <button type="button" @click="$emit('cancel')" class="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            <i class="mdi mdi-check"></i>
            {{ isEdit ? 'Update' : 'Create' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, watch } from 'vue'
import api from '@/services/api'
import IconPicker from '../common/IconPicker.vue'

const props = defineProps({
  device: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['save', 'cancel'])

// Inject SmartIR status
const smartirStatus = inject('smartirStatus')
const smartirInstalled = computed(() => smartirStatus?.value?.installed || false)

const isEdit = computed(() => !!props.device)

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
  area: '',
  icon: '',
  broadlink_entity: '',
  commands: {}
})

const areas = ref([])
const broadlinkDevices = ref([])
const nameInput = ref(null)
const typeSelect = ref(null)
const broadlinkSelect = ref(null)
const iconAutoSet = ref(false) // Track if icon was auto-set vs manually set

onMounted(async () => {
  if (props.device) {
    formData.value = { ...props.device }
  }
  await Promise.all([loadAreas(), loadBroadlinkDevices()])
  
  // Set custom validation messages
  if (nameInput.value) {
    nameInput.value.setCustomValidity('')
    nameInput.value.oninvalid = () => {
      nameInput.value.setCustomValidity('Device name is required')
    }
  }
  if (typeSelect.value) {
    typeSelect.value.setCustomValidity('')
    typeSelect.value.oninvalid = () => {
      typeSelect.value.setCustomValidity('Entity type is required')
    }
  }
  if (broadlinkSelect.value) {
    broadlinkSelect.value.setCustomValidity('')
    broadlinkSelect.value.oninvalid = () => {
      broadlinkSelect.value.setCustomValidity('Broadlink device is required')
    }
  }
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
    const response = await api.get('/api/broadlink/devices')
    // The response is wrapped in a 'devices' property
    const devices = response.data.devices || []
    broadlinkDevices.value = devices
    console.log('Loaded Broadlink devices:', devices)
  } catch (error) {
    console.error('Error loading Broadlink devices:', error)
    broadlinkDevices.value = []
  }
}

const clearValidation = (refName) => {
  const element = refName === 'nameInput' ? nameInput.value : 
                  refName === 'typeSelect' ? typeSelect.value :
                  refName === 'broadlinkSelect' ? broadlinkSelect.value : null
  if (element) {
    element.setCustomValidity('')
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

const handleSubmit = () => {
  // Browser will handle validation with custom messages
  emit('save', { ...formData.value })
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

.smartir-link {
  color: var(--ha-primary-color);
  text-decoration: none;
  font-weight: 600;
  font-size: 12px;
}

.smartir-link:hover {
  text-decoration: underline;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid var(--ha-border-color);
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
