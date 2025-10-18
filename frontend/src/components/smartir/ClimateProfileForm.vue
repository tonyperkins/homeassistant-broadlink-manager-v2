<template>
  <div class="climate-form">
    <h3>Climate Device Configuration</h3>
    
    <!-- Learning Mode Selection -->
    <div class="learning-mode-section">
      <div class="mode-toggle">
        <label class="mode-option" :class="{ active: learningMode === 'quick' }">
          <input type="radio" value="quick" v-model="learningMode" />
          <div class="mode-content">
            <div class="mode-header">
              <i class="mdi mdi-flash"></i>
              <strong>Quick Mode (Recommended)</strong>
            </div>
            <p>Learn one temperature per mode combination</p>
            <div class="mode-stats">
              <span class="stat-badge">{{ quickModeCommands }} commands</span>
              <span class="stat-badge time">~{{ quickModeTime }} min</span>
            </div>
          </div>
        </label>
        
        <label class="mode-option" :class="{ active: learningMode === 'complete' }">
          <input type="radio" value="complete" v-model="learningMode" />
          <div class="mode-content">
            <div class="mode-header">
              <i class="mdi mdi-check-all"></i>
              <strong>Complete Mode</strong>
            </div>
            <p>Learn all temperature combinations</p>
            <div class="mode-stats">
              <span class="stat-badge">{{ completeModeCommands }} commands</span>
              <span class="stat-badge time warning">~{{ completeModeTime }} min</span>
            </div>
          </div>
        </label>
      </div>
      
      <div class="command-breakdown" v-if="learningMode === 'complete'">
        <i class="mdi mdi-information-outline"></i>
        <div>
          <strong>Complete mode will require learning {{ completeModeCommands }} commands</strong>
          <p>This includes all combinations of modes ({{ selectedModesCount }}), temperatures ({{ tempCount }}), fan speeds ({{ selectedFanModesCount }}), and swing modes ({{ selectedSwingModesCount }}).</p>
          <p class="warning-text">⏱️ Estimated time: {{ completeModeTime }} minutes at ~30 seconds per command</p>
        </div>
      </div>
    </div>
    
    <div class="form-section">
      <h4>Temperature Range</h4>
      <p class="help-text" v-if="learningMode === 'quick'">
        Define the full temperature range your device supports. You'll select one temperature to learn below.
      </p>
      <p class="help-text" v-else>
        Define the temperature range. All temperatures in this range will be learned.
      </p>
      
      <div class="form-row">
        <div class="form-group">
          <label>Minimum Temperature (°C) *</label>
          <input 
            v-model.number="config.minTemp" 
            type="number" 
            min="10" 
            max="35"
            placeholder="16"
          />
        </div>
        
        <div class="form-group">
          <label>Maximum Temperature (°C) *</label>
          <input 
            v-model.number="config.maxTemp" 
            type="number" 
            min="10" 
            max="35"
            placeholder="30"
          />
        </div>
        
        <div class="form-group">
          <label>Precision</label>
          <select v-model.number="config.precision">
            <option :value="1">1°C (Whole degrees)</option>
            <option :value="0.5">0.5°C (Half degrees)</option>
          </select>
        </div>
      </div>

      <!-- Quick Mode: Representative Temperature Selection -->
      <div v-if="learningMode === 'quick'" class="representative-temp-section">
        <div class="form-group">
          <label>Representative Temperature to Learn *</label>
          <select v-model.number="config.representativeTemp">
            <option v-for="temp in availableTemps" :key="temp" :value="temp">
              {{ temp }}°C
            </option>
          </select>
          <small>This temperature will be learned for all mode combinations. The device profile will still show the full range ({{ config.minTemp }}°C - {{ config.maxTemp }}°C).</small>
        </div>
      </div>
    </div>

    <div class="form-section">
      <h4>Supported HVAC Modes *</h4>
      <p class="help-text">Select all modes your device supports</p>
      
      <div class="checkbox-grid">
        <label class="checkbox-item">
          <input type="checkbox" value="off" v-model="config.modes" />
          <span class="checkbox-label">
            <i class="mdi mdi-power"></i>
            Off
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="auto" v-model="config.modes" />
          <span class="checkbox-label">
            <i class="mdi mdi-autorenew"></i>
            Auto
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="cool" v-model="config.modes" />
          <span class="checkbox-label">
            <i class="mdi mdi-snowflake"></i>
            Cool
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="heat" v-model="config.modes" />
          <span class="checkbox-label">
            <i class="mdi mdi-fire"></i>
            Heat
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="dry" v-model="config.modes" />
          <span class="checkbox-label">
            <i class="mdi mdi-water-percent"></i>
            Dry
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="fan_only" v-model="config.modes" />
          <span class="checkbox-label">
            <i class="mdi mdi-fan"></i>
            Fan Only
          </span>
        </label>
      </div>
    </div>

    <div class="form-section">
      <h4>Fan Modes</h4>
      <p class="help-text">Select all fan speeds your device supports</p>
      
      <div class="checkbox-grid">
        <label class="checkbox-item">
          <input type="checkbox" value="auto" v-model="config.fanModes" />
          <span class="checkbox-label">
            <i class="mdi mdi-autorenew"></i>
            Auto
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="low" v-model="config.fanModes" />
          <span class="checkbox-label">
            <i class="mdi mdi-fan-speed-1"></i>
            Low
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="medium" v-model="config.fanModes" />
          <span class="checkbox-label">
            <i class="mdi mdi-fan-speed-2"></i>
            Medium
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="high" v-model="config.fanModes" />
          <span class="checkbox-label">
            <i class="mdi mdi-fan-speed-3"></i>
            High
          </span>
        </label>
      </div>
    </div>

    <div class="form-section">
      <h4>Swing Modes (Optional)</h4>
      <p class="help-text">Select if your device has swing/oscillation</p>
      
      <div class="checkbox-grid">
        <label class="checkbox-item">
          <input type="checkbox" value="off" v-model="config.swingModes" />
          <span class="checkbox-label">
            <i class="mdi mdi-swap-horizontal"></i>
            Off
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="vertical" v-model="config.swingModes" />
          <span class="checkbox-label">
            <i class="mdi mdi-swap-vertical"></i>
            Vertical
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="horizontal" v-model="config.swingModes" />
          <span class="checkbox-label">
            <i class="mdi mdi-swap-horizontal"></i>
            Horizontal
          </span>
        </label>
        
        <label class="checkbox-item">
          <input type="checkbox" value="both" v-model="config.swingModes" />
          <span class="checkbox-label">
            <i class="mdi mdi-arrow-all"></i>
            Both
          </span>
        </label>
      </div>
    </div>

    <div class="form-section">
      <h4>Sensors (Optional)</h4>
      <p class="help-text">Link external sensors for better climate control</p>
      
      <div class="form-group">
        <label>Temperature Sensor</label>
        <input 
          v-model="config.tempSensor" 
          type="text" 
          placeholder="sensor.living_room_temperature"
        />
        <small>Entity ID of temperature sensor</small>
      </div>
      
      <div class="form-group">
        <label>Humidity Sensor</label>
        <input 
          v-model="config.humiditySensor" 
          type="text" 
          placeholder="sensor.living_room_humidity"
        />
        <small>Entity ID of humidity sensor</small>
      </div>
      
      <div class="form-group">
        <label>Power Sensor</label>
        <input 
          v-model="config.powerSensor" 
          type="text" 
          placeholder="binary_sensor.ac_power"
        />
        <small>Entity ID of power sensor (to detect on/off state)</small>
      </div>
    </div>

    <div class="validation-summary" v-if="validationErrors.length > 0">
      <h4>
        <i class="mdi mdi-alert-circle"></i>
        Please fix the following:
      </h4>
      <ul>
        <li v-for="(error, index) in validationErrors" :key="index">
          {{ error }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const learningMode = ref('quick')

const config = ref({
  minTemp: 16,
  maxTemp: 30,
  precision: 1,
  representativeTemp: 24,
  modes: ['off', 'auto', 'cool', 'heat'],
  fanModes: ['auto', 'low', 'medium', 'high'],
  swingModes: [],
  tempSensor: '',
  humiditySensor: '',
  powerSensor: '',
  learningMode: 'quick',
  ...props.modelValue
})

// Computed: Available temperatures for dropdown
const availableTemps = computed(() => {
  const temps = []
  const min = config.value.minTemp || 16
  const max = config.value.maxTemp || 30
  const precision = config.value.precision || 1
  
  for (let temp = min; temp <= max; temp += precision) {
    temps.push(temp)
  }
  
  return temps
})

// Computed: Count selected options
const selectedModesCount = computed(() => {
  // Count modes that need temperature (exclude 'off')
  return config.value.modes.filter(m => m !== 'off').length
})

const selectedFanModesCount = computed(() => {
  return config.value.fanModes.length || 1
})

const selectedSwingModesCount = computed(() => {
  return config.value.swingModes.length || 1
})

const tempCount = computed(() => {
  const min = config.value.minTemp || 16
  const max = config.value.maxTemp || 30
  const precision = config.value.precision || 1
  return Math.floor((max - min) / precision) + 1
})

// Computed: Quick mode commands (one temp per combination + off)
const quickModeCommands = computed(() => {
  const hasOff = config.value.modes.includes('off') ? 1 : 0
  const combinations = selectedModesCount.value * selectedFanModesCount.value * selectedSwingModesCount.value
  return combinations + hasOff
})

const quickModeTime = computed(() => {
  return Math.ceil((quickModeCommands.value * 30) / 60) // 30 seconds per command
})

// Computed: Complete mode commands (all temps for all combinations + off)
const completeModeCommands = computed(() => {
  const hasOff = config.value.modes.includes('off') ? 1 : 0
  const combinations = selectedModesCount.value * tempCount.value * selectedFanModesCount.value * selectedSwingModesCount.value
  return combinations + hasOff
})

const completeModeTime = computed(() => {
  return Math.ceil((completeModeCommands.value * 30) / 60) // 30 seconds per command
})

const validationErrors = computed(() => {
  const errors = []
  
  if (!config.value.minTemp || config.value.minTemp < 10 || config.value.minTemp > 35) {
    errors.push('Minimum temperature must be between 10°C and 35°C')
  }
  
  if (!config.value.maxTemp || config.value.maxTemp < 10 || config.value.maxTemp > 35) {
    errors.push('Maximum temperature must be between 10°C and 35°C')
  }
  
  if (config.value.minTemp >= config.value.maxTemp) {
    errors.push('Minimum temperature must be less than maximum temperature')
  }
  
  if (!config.value.modes || config.value.modes.length === 0) {
    errors.push('At least one HVAC mode must be selected')
  }
  
  return errors
})

watch(learningMode, (newValue) => {
  config.value.learningMode = newValue
})

watch(config, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true, immediate: true })
</script>

<style scoped>
.climate-form {
  max-width: 800px;
}

.climate-form h3 {
  margin: 0 0 24px 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-text-color);
}

/* Learning Mode Section */
.learning-mode-section {
  margin-bottom: 32px;
  padding: 20px;
  background: var(--ha-card-background);
  border: 2px solid var(--ha-border-color);
  border-radius: 12px;
}

.mode-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.mode-option {
  position: relative;
  padding: 16px;
  border: 2px solid var(--ha-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-option:hover {
  border-color: var(--primary-color);
  background: rgba(3, 169, 244, 0.05);
}

.mode-option.active {
  border-color: var(--primary-color);
  background: rgba(3, 169, 244, 0.1);
}

.mode-option input[type="radio"] {
  position: absolute;
  opacity: 0;
}

.mode-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mode-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--primary-text-color);
}

.mode-header i {
  font-size: 20px;
  color: var(--primary-color);
}

.mode-content p {
  margin: 0;
  font-size: 13px;
  color: var(--secondary-text-color);
}

.mode-stats {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.stat-badge {
  padding: 4px 10px;
  background: var(--ha-divider-color);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.stat-badge.time {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.stat-badge.time.warning {
  background: rgba(255, 152, 0, 0.1);
  color: #ff9800;
}

.command-breakdown {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 152, 0, 0.1);
  border-left: 4px solid #ff9800;
  border-radius: 6px;
}

.command-breakdown i {
  font-size: 24px;
  color: #ff9800;
  flex-shrink: 0;
}

.command-breakdown strong {
  display: block;
  margin-bottom: 8px;
  color: var(--primary-text-color);
}

.command-breakdown p {
  margin: 4px 0;
  font-size: 13px;
  color: var(--secondary-text-color);
}

.warning-text {
  color: #ff9800 !important;
  font-weight: 600;
}

.representative-temp-section {
  margin-top: 16px;
  padding: 16px;
  background: rgba(3, 169, 244, 0.05);
  border: 1px solid rgba(3, 169, 244, 0.3);
  border-radius: 8px;
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--ha-border-color);
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.help-text {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: var(--secondary-text-color);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: var(--primary-text-color);
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--ha-border-color);
  border-radius: 6px;
  background: var(--ha-card-background);
  color: var(--primary-text-color);
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-group small {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--secondary-text-color);
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border: 2px solid var(--ha-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--ha-card-background);
}

.checkbox-item:hover {
  border-color: var(--primary-color);
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
}

.checkbox-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-item input[type="checkbox"]:checked + .checkbox-label {
  color: var(--primary-color);
  font-weight: 600;
}

.checkbox-item:has(input:checked) {
  border-color: var(--primary-color);
  background: rgba(var(--primary-color-rgb, 3, 169, 244), 0.1);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--primary-text-color);
  font-size: 14px;
  user-select: none;
}

.checkbox-label i {
  font-size: 18px;
}

.validation-summary {
  margin-top: 24px;
  padding: 16px;
  background: rgba(244, 67, 54, 0.1);
  border-left: 4px solid #f44336;
  border-radius: 4px;
}

.validation-summary h4 {
  margin: 0 0 12px 0;
  color: #f44336;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

.validation-summary ul {
  margin: 0;
  padding-left: 20px;
}

.validation-summary li {
  color: var(--primary-text-color);
  font-size: 13px;
  margin-bottom: 4px;
}

/* Dark mode adjustments */
:global(.dark-mode) .checkbox-item {
  background: rgba(255, 255, 255, 0.03);
}

:global(.dark-mode) .checkbox-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

:global(.dark-mode) .validation-summary {
  background: rgba(244, 67, 54, 0.15);
}
</style>
