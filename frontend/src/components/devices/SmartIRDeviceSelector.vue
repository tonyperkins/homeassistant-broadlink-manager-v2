<template>
  <div class="smartir-selector">
    <!-- Manufacturer Selection -->
    <div class="form-group">
      <SearchableDropdown
        v-model="selectedManufacturer"
        :options="manufacturers"
        label="Manufacturer"
        placeholder="Search manufacturers..."
        required
        :loading="loadingManufacturers"
        :error="errors.manufacturer"
        hint="Select the device manufacturer"
        @change="handleManufacturerChange"
      />
    </div>

    <!-- Model Selection -->
    <div class="form-group">
      <SearchableDropdown
        v-model="selectedModel"
        :options="models"
        :option-label="'label'"
        :option-value="'code'"
        :option-description="'description'"
        label="Model"
        placeholder="Search models..."
        required
        :disabled="!selectedManufacturer"
        :loading="loadingModels"
        :error="errors.model"
        hint="Select the device model"
        @change="handleModelChange"
      />
    </div>

    <!-- Controller Device Selection -->
    <div class="form-group">
      <label for="controller-device">
        <i class="mdi mdi-remote"></i>
        Controller Device *
      </label>
      <select
        id="controller-device"
        v-model="selectedController"
        required
        @change="handleControllerChange"
      >
        <option value="">-- Select Controller Device --</option>
        <option
          v-for="device in broadlinkDevices"
          :key="device.entity_id"
          :value="device.entity_id"
        >
          {{ device.name || device.entity_id }}
          <template v-if="device.area_name"> - {{ device.area_name }}</template>
        </option>
      </select>
      <small>Which remote device will send the IR/RF commands</small>
      <div v-if="errors.controller" class="error-message">{{ errors.controller }}</div>
    </div>

    <!-- Climate-specific fields -->
    <template v-if="entityType === 'climate'">
      <div class="form-group">
        <label for="temperature-sensor">Temperature Sensor</label>
        <input
          id="temperature-sensor"
          v-model="temperatureSensor"
          type="text"
          placeholder="e.g., sensor.living_room_temperature"
          @input="handleTemperatureSensorChange"
        />
        <small>Optional: Temperature sensor entity for current temperature</small>
      </div>

      <div class="form-group">
        <label for="humidity-sensor">Humidity Sensor</label>
        <input
          id="humidity-sensor"
          v-model="humiditySensor"
          type="text"
          placeholder="e.g., sensor.living_room_humidity"
          @input="handleHumiditySensorChange"
        />
        <small>Optional: Humidity sensor entity for current humidity</small>
      </div>
    </template>

    <!-- Selected Code Info -->
    <div v-if="selectedCodeInfo" class="code-info">
      <div class="info-header">
        <i class="mdi mdi-information"></i>
        <span>Selected Device Code</span>
      </div>
      <div class="info-content">
        <div class="info-row">
          <span class="info-label">Code ID:</span>
          <span class="info-value">{{ selectedCodeInfo.code_id }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Manufacturer:</span>
          <span class="info-value">{{ selectedCodeInfo.manufacturer }}</span>
        </div>
        <div v-if="selectedCodeInfo.models && selectedCodeInfo.models.length > 0" class="info-row">
          <span class="info-label">Supported Models:</span>
          <span class="info-value">{{ selectedCodeInfo.models.join(', ') }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Controller:</span>
          <span class="info-value">{{ selectedCodeInfo.controller || 'Broadlink' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'
import SearchableDropdown from '../common/SearchableDropdown.vue'

const props = defineProps({
  entityType: {
    type: String,
    required: true
  },
  modelValue: {
    type: Object,
    default: () => ({})
  },
  broadlinkDevices: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// State
const manufacturers = ref([])
const models = ref([])
const selectedManufacturer = ref('')
const selectedModel = ref('')
const selectedController = ref('')
const temperatureSensor = ref('')
const humiditySensor = ref('')
const selectedCodeInfo = ref(null)

const loadingManufacturers = ref(false)
const loadingModels = ref(false)

const errors = ref({
  manufacturer: '',
  model: '',
  controller: ''
})

// Load manufacturers on mount
onMounted(async () => {
  await loadManufacturers()
  
  // Initialize from modelValue if provided
  if (props.modelValue) {
    selectedManufacturer.value = props.modelValue.manufacturer || ''
    selectedModel.value = props.modelValue.device_code || ''
    selectedController.value = props.modelValue.controller_device || ''
    temperatureSensor.value = props.modelValue.temperature_sensor || ''
    humiditySensor.value = props.modelValue.humidity_sensor || ''
    
    // Load models if manufacturer is set
    if (selectedManufacturer.value) {
      await loadModels(selectedManufacturer.value)
      
      // Set selectedCodeInfo after models are loaded
      if (selectedModel.value && models.value.length > 0) {
        const matchingModel = models.value.find(m => m.code === selectedModel.value)
        if (matchingModel) {
          selectedCodeInfo.value = {
            code: matchingModel.code,
            manufacturer: selectedManufacturer.value,
            models: matchingModel.models,
            controller: matchingModel.controller
          }
        }
      }
    }
  }
})

// Watch entity type changes
watch(() => props.entityType, async (newType) => {
  if (newType) {
    // Reset selections when entity type changes
    selectedManufacturer.value = ''
    selectedModel.value = ''
    models.value = []
    selectedCodeInfo.value = null
    await loadManufacturers()
  }
})

const loadManufacturers = async () => {
  if (!props.entityType) return
  
  loadingManufacturers.value = true
  errors.value.manufacturer = ''
  
  try {
    const response = await api.get('/api/smartir/codes/manufacturers', {
      params: { entity_type: props.entityType }
    })
    
    if (response.data.success) {
      manufacturers.value = response.data.manufacturers || []
    } else {
      throw new Error(response.data.error || 'Failed to load manufacturers')
    }
  } catch (error) {
    console.error('Error loading manufacturers:', error)
    errors.value.manufacturer = 'Failed to load manufacturers. Please try again.'
    manufacturers.value = []
  } finally {
    loadingManufacturers.value = false
  }
}

const loadModels = async (manufacturer) => {
  if (!manufacturer || !props.entityType) return
  
  loadingModels.value = true
  errors.value.model = ''
  
  try {
    const response = await api.get('/api/smartir/codes/models', {
      params: {
        entity_type: props.entityType,
        manufacturer: manufacturer
      }
    })
    
    if (response.data.success) {
      const modelData = response.data.models || []
      
      // Transform models for dropdown
      models.value = modelData.map(model => {
        const modelNames = model.models && model.models.length > 0 
          ? model.models.join(', ') 
          : `Code ${model.code_id}`
        
        return {
          code_id: model.code_id,
          label: modelNames,  // Show model names as label
          description: `Code: ${model.code_id}`,  // Show code as description
          models: model.models,
          controller: model.controller
        }
      })
    } else {
      throw new Error(response.data.error || 'Failed to load models')
    }
  } catch (error) {
    console.error('Error loading models:', error)
    errors.value.model = 'Failed to load models. Please try again.'
    models.value = []
  } finally {
    loadingModels.value = false
  }
}

const handleManufacturerChange = async (value) => {
  selectedManufacturer.value = value
  selectedModel.value = ''
  selectedCodeInfo.value = null
  models.value = []
  
  if (value) {
    await loadModels(value)
  }
  
  emitChange()
}

const handleModelChange = () => {
  // Find the selected model info
  const modelInfo = models.value.find(m => m.code === selectedModel.value)
  if (modelInfo) {
    selectedCodeInfo.value = {
      code: modelInfo.code,
      manufacturer: selectedManufacturer.value,
      models: modelInfo.models,
      controller: modelInfo.controller
    }
  }
  emitChange()
}

const handleControllerChange = () => {
  emitChange()
}

const handleTemperatureSensorChange = () => {
  emitChange()
}

const handleHumiditySensorChange = () => {
  emitChange()
}

const emitChange = () => {
  const data = {
    manufacturer: selectedManufacturer.value,
    model: selectedCodeInfo.value?.models?.[0] || '',
    device_code: selectedModel.value,
    controller_device: selectedController.value,
  }
  
  // Add climate-specific fields
  if (props.entityType === 'climate') {
    if (temperatureSensor.value) {
      data.temperature_sensor = temperatureSensor.value
    }
    if (humiditySensor.value) {
      data.humidity_sensor = humiditySensor.value
    }
  }
  
  emit('update:modelValue', data)
  emit('change', data)
}

// Validation
const validate = () => {
  let isValid = true
  errors.value = {
    manufacturer: '',
    model: '',
    controller: ''
  }
  
  if (!selectedManufacturer.value) {
    errors.value.manufacturer = 'Manufacturer is required'
    isValid = false
  }
  
  if (!selectedModel.value) {
    errors.value.model = 'Model is required'
    isValid = false
  }
  
  if (!selectedController.value) {
    errors.value.controller = 'Broadlink controller is required'
    isValid = false
  }
  
  return isValid
}

// Expose validate method
defineExpose({
  validate
})
</script>

<style scoped>
.smartir-selector {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: var(--ha-text-primary-color);
  font-size: 14px;
}

.form-group select,
.form-group input[type="text"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--ha-divider-color, #e0e0e0);
  border-radius: 8px;
  font-size: 14px;
  background: var(--ha-card-background);
  color: var(--ha-text-primary-color);
  transition: all 0.2s;
}

.form-group select:focus,
.form-group input[type="text"]:focus {
  outline: none;
  border-color: var(--ha-primary-color, #03a9f4);
  box-shadow: 0 0 0 3px rgba(3, 169, 244, 0.1);
}

.form-group select:disabled,
.form-group input[type="text"]:disabled {
  background: var(--ha-disabled-background, #f5f5f5);
  cursor: not-allowed;
  opacity: 0.6;
}

.form-group small {
  font-size: 12px;
  color: var(--ha-text-secondary-color);
}

.error-message {
  font-size: 12px;
  color: var(--ha-error-color, #f44336);
  margin-top: 4px;
}

.code-info {
  background: var(--ha-card-background);
  border: 1px solid var(--ha-divider-color, #e0e0e0);
  border-radius: 8px;
  padding: 16px;
  margin-top: 8px;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--ha-primary-color, #03a9f4);
}

.info-header i {
  font-size: 20px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.info-label {
  font-weight: 500;
  color: var(--ha-text-secondary-color);
  min-width: 140px;
}

.info-value {
  color: var(--ha-text-primary-color);
  flex: 1;
}
</style>
