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
            v-model="formData.name"
            type="text"
            placeholder="e.g., Living Room TV"
            required
          />
        </div>

        <div class="form-group">
          <label for="entity-type">Entity Type *</label>
          <select id="entity-type" v-model="formData.entity_type" required>
            <option value="">-- Select Type --</option>
            <option value="light">Light</option>
            <option value="fan">Fan</option>
            <option value="switch">Switch</option>
            <option value="media_player">Media Player (Universal)</option>
            <option value="cover">Cover (Blinds/Curtains)</option>
          </select>
          <small>Note: For climate control (AC/Heater), use SmartIR integration</small>
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
            v-model="formData.broadlink_entity"
            required
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
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import IconPicker from '../common/IconPicker.vue'

const props = defineProps({
  device: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['save', 'cancel'])

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

onMounted(async () => {
  if (props.device) {
    formData.value = { ...props.device }
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

const handleSubmit = () => {
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
