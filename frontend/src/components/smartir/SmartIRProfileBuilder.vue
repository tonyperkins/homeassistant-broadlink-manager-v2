<template>
  <div v-if="show" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <div class="modal-header">
        <h2>
          <i class="mdi mdi-file-document-edit"></i>
          {{ editMode ? 'Edit SmartIR Profile' : 'Create SmartIR Profile' }}
        </h2>
        <button @click="close" class="close-button">
          <i class="mdi mdi-close"></i>
        </button>
      </div>

      <!-- Progress Steps -->
      <div class="progress-steps">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="step"
          :class="{
            'active': currentStep === index,
            'completed': currentStep > index
          }"
        >
          <div class="step-number">
            <i v-if="currentStep > index" class="mdi mdi-check"></i>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <span class="step-label">{{ step.label }}</span>
        </div>
      </div>

      <div class="modal-body">
        <!-- Step 1: Platform & Device Info -->
        <div v-if="currentStep === 0" class="step-content">
          <h3>Device Information</h3>
          
          <div class="form-group">
            <label>Platform Type *</label>
            <select v-model="profile.platform" @change="handlePlatformChange">
              <option value="">Select platform...</option>
              <option value="climate">🌡️ Climate (AC, Heater, Heat Pump)</option>
              <option value="media_player">📺 Media Player (TV, Receiver)</option>
              <option value="fan">🌀 Fan</option>
            </select>
          </div>

          <div class="form-group">
            <label>Manufacturer *</label>
            <input 
              v-model="profile.manufacturer" 
              type="text" 
              placeholder="e.g., Daikin, LG, Samsung"
            />
          </div>

          <div class="form-group">
            <label>Model(s) *</label>
            <input 
              v-model="profile.model" 
              type="text" 
              placeholder="e.g., FTXS35K, Multiple models"
            />
            <small>Enter model number or "Multiple" if it works with many models</small>
          </div>

          <div class="form-group">
            <label>Broadlink Device *</label>
            <select v-model="profile.broadlinkDevice">
              <option value="">Select Broadlink device...</option>
              <option 
                v-for="device in broadlinkDevices" 
                :key="device.entity_id"
                :value="device.entity_id"
              >
                {{ device.name }} ({{ device.area_name }})
              </option>
            </select>
            <small>This device will be used to learn commands ({{ broadlinkDevices.length }} devices found)</small>
          </div>

          <div class="form-group">
            <label>Command Type *</label>
            <select v-model="profile.commandType">
              <option value="ir">📡 Infrared (IR) - Most common for AC, TV, etc.</option>
              <option value="rf">📻 Radio Frequency (RF) - For RF remotes</option>
            </select>
            <small>Select the type of commands your device uses</small>
          </div>
        </div>

        <!-- Step 2: Platform-Specific Configuration -->
        <div v-if="currentStep === 1" class="step-content">
          <ClimateProfileForm 
            v-if="profile.platform === 'climate'"
            v-model="profile.config"
          />
          
          <div v-else-if="profile.platform === 'media_player'" class="platform-form">
            <h3>Media Player Configuration</h3>
            <p class="info-message">
              <i class="mdi mdi-information"></i>
              Media player profiles coming soon! For now, focus on climate devices.
            </p>
          </div>

          <div v-else-if="profile.platform === 'fan'" class="platform-form">
            <h3>Fan Configuration</h3>
            <p class="info-message">
              <i class="mdi mdi-information"></i>
              Fan profiles coming soon! For now, focus on climate devices.
            </p>
          </div>
        </div>

        <!-- Step 3: Learn Commands -->
        <div v-if="currentStep === 2" class="step-content">
          <CommandLearningWizard
            v-model="profile.commands"
            :platform="profile.platform"
            :config="profile.config"
            :broadlinkDevice="profile.broadlinkDevice"
            :manufacturer="profile.manufacturer"
            :model="profile.model"
            :commandType="profile.commandType"
          />
        </div>

        <!-- Step 4: Preview & Save -->
        <div v-if="currentStep === 3" class="step-content">
          <ProfilePreview
            :profile="profile"
            :json-data="generatedJson"
            :yaml-config="generatedYaml"
          />
        </div>
      </div>

      <div class="modal-footer">
        <button 
          v-if="currentStep > 0" 
          @click="previousStep" 
          class="btn-secondary"
        >
          <i class="mdi mdi-arrow-left"></i>
          Back
        </button>
        
        <div class="spacer"></div>
        
        <button @click="close" class="btn-text">
          Cancel
        </button>
        
        <button 
          v-if="currentStep < steps.length - 1"
          @click="nextStep" 
          class="btn-primary"
          :disabled="!canProceed"
        >
          Next
          <i class="mdi mdi-arrow-right"></i>
        </button>
        
        <div v-else class="save-buttons">
          <button 
            @click="saveToSmartIR" 
            class="btn-primary"
            :disabled="saving"
          >
            <i class="mdi mdi-cloud-upload"></i>
            {{ saving ? 'Saving...' : 'Save to SmartIR' }}
          </button>
          
          <button 
            @click="downloadLocally" 
            class="btn-secondary"
            :disabled="saving"
          >
            <i class="mdi mdi-download"></i>
            Download JSON
          </button>
        </div>
      </div>
    </div>

    <!-- Setup Wizard -->
    <SmartIRSetupWizard
      :show="showSetupWizard"
      :platform="profile.platform"
      :warnings="configWarnings"
      :config-path="configPath"
      @close="showSetupWizard = false"
      @complete="completeSetup"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import ClimateProfileForm from './ClimateProfileForm.vue'
import CommandLearningWizard from './CommandLearningWizard.vue'
import ProfilePreview from './ProfilePreview.vue'
import SmartIRSetupWizard from './SmartIRSetupWizard.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  editMode: {
    type: Boolean,
    default: false
  },
  editData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

const toastRef = inject('toast')

const currentStep = ref(0)
const saving = ref(false)
const broadlinkDevices = ref([])
const showSetupWizard = ref(false)
const configWarnings = ref([])
const configPath = ref('/config')
const setupCompleted = ref(false)
const pendingSaveData = ref(null)

const steps = [
  { label: 'Device Info', key: 'info' },
  { label: 'Configuration', key: 'config' },
  { label: 'Learn Commands', key: 'commands' },
  { label: 'Preview & Save', key: 'preview' }
]

const profile = ref({
  platform: '',
  manufacturer: '',
  model: '',
  broadlinkDevice: '',
  commandType: 'ir', // Default to IR
  config: {},
  commands: {}
})

// Helper functions to infer modes from command keys
function inferModesFromCommands(commands) {
  const modes = new Set()
  const commandKeys = Object.keys(commands)
  
  // Check for specific mode patterns
  if (commandKeys.some(k => k === 'off' || k.includes('_off'))) modes.add('off')
  if (commandKeys.some(k => k.includes('auto'))) modes.add('auto')
  if (commandKeys.some(k => k.includes('cool'))) modes.add('cool')
  if (commandKeys.some(k => k.includes('heat'))) modes.add('heat')
  if (commandKeys.some(k => k.includes('dry'))) modes.add('dry')
  if (commandKeys.some(k => k.includes('fan_only'))) modes.add('fan_only')
  
  return Array.from(modes)
}

function inferFanModesFromCommands(commands) {
  const fanModes = new Set()
  const commandKeys = Object.keys(commands)
  
  // Check for fan speed patterns in command keys
  if (commandKeys.some(k => k.includes('auto'))) fanModes.add('auto')
  if (commandKeys.some(k => k.includes('low'))) fanModes.add('low')
  if (commandKeys.some(k => k.includes('medium') || k.includes('mid'))) fanModes.add('medium')
  if (commandKeys.some(k => k.includes('high'))) fanModes.add('high')
  
  return Array.from(fanModes)
}

function inferSwingModesFromCommands(commands) {
  const swingModes = new Set()
  const commandKeys = Object.keys(commands)
  
  // Check for swing patterns
  if (commandKeys.some(k => k.includes('swing_off') || k.includes('_off'))) swingModes.add('off')
  if (commandKeys.some(k => k.includes('vertical'))) swingModes.add('vertical')
  if (commandKeys.some(k => k.includes('horizontal'))) swingModes.add('horizontal')
  if (commandKeys.some(k => k.includes('both'))) swingModes.add('both')
  
  return Array.from(swingModes)
}

// Watch for edit data and populate profile
watch(() => props.editData, async (newData) => {
  if (newData && props.editMode) {
    console.log('🔧 Edit mode activated, loading profile data:', newData)
    
    // Ensure Broadlink devices are loaded first
    if (broadlinkDevices.value.length === 0) {
      console.log('📡 Loading Broadlink devices...')
      await loadBroadlinkDevices()
      console.log('📡 Devices loaded:', broadlinkDevices.value.length)
    }
    
    const profileData = newData.profile
    const controllerData = profileData.controller_data
    console.log('🎮 Controller data from profile:', controllerData)
    console.log('🎮 Available devices:', broadlinkDevices.value.map(d => d.entity_id))
    
    // Infer modes from commands if not explicitly defined
    const commands = profileData.commands || {}
    const inferredModes = profileData.operationModes || inferModesFromCommands(commands)
    const inferredFanModes = profileData.fanModes || inferFanModesFromCommands(commands)
    const inferredSwingModes = profileData.swingModes || inferSwingModesFromCommands(commands)
    
    console.log('🔍 Inferred modes:', inferredModes)
    console.log('🔍 Inferred fan modes:', inferredFanModes)
    console.log('🔍 Inferred swing modes:', inferredSwingModes)
    
    profile.value = {
      platform: newData.platform,
      manufacturer: profileData.manufacturer || '',
      model: profileData.supportedModels?.[0] || '',
      broadlinkDevice: controllerData || '',
      config: {
        minTemp: profileData.minTemperature,
        maxTemp: profileData.maxTemperature,
        precision: profileData.precision,
        modes: inferredModes,
        fanModes: inferredFanModes,
        swingModes: inferredSwingModes
      },
      commands: commands
    }
    
    console.log('✅ Profile populated:', profile.value)
    console.log('✅ Selected device:', profile.value.broadlinkDevice)
  }
}, { immediate: true })

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return profile.value.platform && 
             profile.value.manufacturer && 
             profile.value.model &&
             profile.value.broadlinkDevice &&
             profile.value.commandType
    case 1:
      // Platform-specific validation
      if (profile.value.platform === 'climate') {
        return profile.value.config.minTemp && 
               profile.value.config.maxTemp &&
               profile.value.config.modes?.length > 0
      }
      return true
    case 2:
      // At least some commands learned
      return Object.keys(profile.value.commands).length > 0
    case 3:
      return true
    default:
      return false
  }
})

const generatedJson = computed(() => {
  if (currentStep.value !== 3) return null
  
  return generateSmartIRJson(profile.value)
})

const generatedYaml = computed(() => {
  if (currentStep.value !== 3) return null
  
  return generateYamlConfig(profile.value)
})

function handlePlatformChange() {
  // Reset config when platform changes
  profile.value.config = {}
  profile.value.commands = {}
}

function nextStep() {
  if (canProceed.value && currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function previousStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function handleOverlayClick() {
  if (confirm('Are you sure you want to close? Your progress will be lost.')) {
    close()
  }
}

function close() {
  emit('close')
  // Reset after animation
  setTimeout(() => {
    currentStep.value = 0
    profile.value = {
      platform: '',
      manufacturer: '',
      model: '',
      broadlinkDevice: '',
      config: {},
      commands: {}
    }
  }, 300)
}

async function saveToSmartIR() {
  saving.value = true
  
  try {
    // Check if setup is needed
    if (!setupCompleted.value) {
      const configCheck = await fetch('/api/smartir/config/check')
      if (configCheck.ok) {
        const configStatus = await configCheck.json()
        
        // Check if platform file exists
        const platformExists = configStatus.platforms[profile.value.platform]?.file_exists
        
        if (!platformExists) {
          // Show setup wizard
          configWarnings.value = configStatus.configuration_warnings || []
          configPath.value = configStatus.config_path || '/config'
          
          // Store the save data for after setup
          pendingSaveData.value = {
            platform: profile.value.platform,
            json: generatedJson.value
          }
          
          showSetupWizard.value = true
          saving.value = false
          return
        }
      }
    }
    
    // Get code number - use existing code if editing, otherwise get next available
    let codeNumber
    if (props.editMode && props.editData?.code) {
      // Use existing code when editing
      codeNumber = parseInt(props.editData.code)
      console.log('📝 Edit mode: Using existing code', codeNumber)
    } else {
      // Get next available code for new profile
      const codeResponse = await fetch(`/api/smartir/platforms/${profile.value.platform}/next-code`)
      if (!codeResponse.ok) {
        throw new Error('Failed to get next code number')
      }
      
      const codeData = await codeResponse.json()
      codeNumber = codeData.next_code
      console.log('✨ New profile: Using next code', codeNumber)
    }
    
    // Save profile to SmartIR directory
    const response = await fetch('/api/smartir/profiles', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform: profile.value.platform,
        json: generatedJson.value,
        code_number: codeNumber
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to save profile')
    }
    
    const result = await response.json()
    
    // Add device to configuration file
    const deviceConfig = {
      name: `${profile.value.manufacturer} ${profile.value.model}`,
      unique_id: `${profile.value.manufacturer.toLowerCase().replace(/[^a-z0-9]+/g, '_')}_${profile.value.model.toLowerCase().replace(/[^a-z0-9]+/g, '_')}`,
      device_code: codeNumber,
      controller_data: profile.value.broadlinkDevice
    }
    
    const configResponse = await fetch('/api/smartir/config/add-device', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform: profile.value.platform,
        device_config: deviceConfig
      })
    })
    
    if (!configResponse.ok) {
      const configError = await configResponse.json()
      console.error('Failed to add device to config:', configError)
      toastRef.value?.warning(
        `Profile saved but failed to add to config file: ${configError.error}`,
        '⚠️ Partial Success'
      )
    }
    
    // Emit save event
    emit('save', {
      json: generatedJson.value,
      yaml: generatedYaml.value,
      profile: profile.value,
      saved_to: result.path
    })
    
    // Show success message
    toastRef.value?.success(
      `File: ${result.filename}\nDevice Code: ${codeNumber}\nAdded to: smartir/${profile.value.platform}.yaml\n\n⚠️ Restart Home Assistant to activate`,
      '✅ Profile Saved Successfully!'
    )
    
    close()
  } catch (error) {
    console.error('Error saving profile:', error)
    toastRef.value?.error(error.message, '❌ Error Saving Profile')
  } finally {
    saving.value = false
  }
}

async function completeSetup() {
  setupCompleted.value = true
  showSetupWizard.value = false
  
  // Continue with the save that was interrupted
  if (pendingSaveData.value) {
    await saveToSmartIR()
    pendingSaveData.value = null
  }
}

function downloadLocally() {
  try {
    // Create blob from JSON
    const jsonString = JSON.stringify(generatedJson.value, null, 2)
    const blob = new Blob([jsonString], { type: 'application/json' })
    
    // Create download link
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // Generate filename
    const manufacturer = profile.value.manufacturer.toLowerCase().replace(/\s+/g, '_')
    const model = profile.value.model.toLowerCase().replace(/\s+/g, '_')
    link.download = `smartir_${profile.value.platform}_${manufacturer}_${model}.json`
    
    // Trigger download
    document.body.appendChild(link)
    link.click()
    
    // Cleanup
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    toastRef.value?.success(
      'You can manually upload this file to your SmartIR codes directory.',
      '✅ Profile Downloaded'
    )
  } catch (error) {
    console.error('Error downloading profile:', error)
    toastRef.value?.error(error.message, '❌ Error Downloading Profile')
  }
}

function generateSmartIRJson(profile) {
  const json = {
    manufacturer: profile.manufacturer,
    supportedModels: [profile.model],
    supportedController: "Broadlink",
    commandsEncoding: "Base64",
    commands: {}
  }
  
  if (profile.platform === 'climate') {
    json.minTemperature = profile.config.minTemp
    json.maxTemperature = profile.config.maxTemp
    json.precision = profile.config.precision || 1
    json.operationModes = profile.config.modes || []
    
    // SmartIR requires at least one fan mode - default to 'auto' if none selected
    json.fanModes = (profile.config.fanModes && profile.config.fanModes.length > 0) 
      ? profile.config.fanModes 
      : ['auto']
    
    // Add swing modes if configured
    if (profile.config.swingModes && profile.config.swingModes.length > 0) {
      json.swingModes = profile.config.swingModes
    }
    
    // Add temperature commands
    json.commands = profile.commands
  }
  
  return json
}

function generateYamlConfig(profile) {
  let yaml = `# SmartIR ${profile.platform} configuration\n`
  yaml += `# Generated by Broadlink Manager v2\n\n`
  
  if (profile.platform === 'climate') {
    yaml += `climate:\n`
    yaml += `  - platform: smartir\n`
    yaml += `    name: ${profile.manufacturer} ${profile.model}\n`
    yaml += `    unique_id: ${profile.manufacturer.toLowerCase()}_${profile.model.toLowerCase().replace(/\s+/g, '_')}\n`
    yaml += `    device_code: 10000  # Change this to your custom code number\n`
    yaml += `    controller_data: ${profile.broadlinkDevice}\n`
    
    if (profile.config.tempSensor) {
      yaml += `    temperature_sensor: ${profile.config.tempSensor}\n`
    }
    if (profile.config.humiditySensor) {
      yaml += `    humidity_sensor: ${profile.config.humiditySensor}\n`
    }
    if (profile.config.powerSensor) {
      yaml += `    power_sensor: ${profile.config.powerSensor}\n`
    }
  }
  
  return yaml
}

async function loadBroadlinkDevices() {
  try {
    console.log('Fetching Broadlink devices from /api/broadlink/devices...')
    const response = await fetch('/api/broadlink/devices')
    console.log('Response status:', response.status, response.ok)
    
    if (response.ok) {
      const data = await response.json()
      console.log('Loaded Broadlink devices response:', data)
      
      // The API wraps the devices in a 'devices' property
      const devices = data.devices || []
      console.log('Extracted devices array:', devices)
      console.log('Device count:', devices.length)
      
      broadlinkDevices.value = devices
      console.log('broadlinkDevices.value set to:', broadlinkDevices.value)
      console.log('Final device count:', broadlinkDevices.value.length)
    } else {
      console.error('Response not OK:', response.status, response.statusText)
      broadlinkDevices.value = []
    }
  } catch (error) {
    console.error('Error loading Broadlink devices:', error)
    broadlinkDevices.value = []
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadBroadlinkDevices()
  }
})

onMounted(() => {
  if (props.show) {
    loadBroadlinkDevices()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-container {
  background: var(--ha-card-background);
  border-radius: 12px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
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
  font-weight: 600;
  color: var(--primary-text-color);
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-header h2 i {
  color: var(--ha-primary-color);
}

.close-button {
  background: transparent;
  border: none;
  color: var(--secondary-text-color);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-button:hover {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
  color: var(--primary-text-color);
}

.close-button i {
  font-size: 24px;
}

/* Progress Steps */
.progress-steps {
  display: flex;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid var(--ha-border-color);
  background: var(--ha-card-header-background, var(--ha-card-background));
}

.step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
}

.step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 16px;
  left: 50%;
  right: -50%;
  height: 2px;
  background: var(--ha-border-color);
  z-index: 0;
}

.step.completed:not(:last-child)::after {
  background: var(--ha-primary-color);
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--ha-border-color);
  color: var(--secondary-text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  position: relative;
  z-index: 1;
  transition: all 0.3s;
}

.step.active .step-number {
  background: var(--ha-primary-color);
  color: white;
  transform: scale(1.1);
}

.step.completed .step-number {
  background: var(--ha-primary-color);
  color: white;
}

.step-label {
  font-size: 12px;
  color: var(--secondary-text-color);
  text-align: center;
}

.step.active .step-label {
  color: var(--primary-text-color);
  font-weight: 600;
}

/* Modal Body */
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.step-content {
  animation: fadeInContent 0.3s ease-out;
}

@keyframes fadeInContent {
  from {
    opacity: 0;
    transform: translateX(10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.step-content h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-text-color);
}

/* Form Groups */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
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
  border-color: var(--ha-primary-color);
}

.form-group small {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--secondary-text-color);
}

.info-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(33, 150, 243, 0.1);
  border-left: 4px solid #2196f3;
  border-radius: 4px;
  color: var(--primary-text-color);
}

.info-message i {
  font-size: 24px;
  color: #2196f3;
}

/* Modal Footer */
.modal-footer {
  display: flex;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--ha-border-color);
  background: var(--ha-card-header-background, var(--ha-card-background));
}

.spacer {
  flex: 1;
}

.save-buttons {
  display: flex;
  gap: 12px;
}

.btn-primary,
.btn-secondary,
.btn-text {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: var(--ha-primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  color: var(--ha-primary-color);
  border: 1px solid var(--ha-primary-color);
}

.btn-secondary:hover {
  background: var(--ha-primary-color);
  color: white;
}

.btn-text {
  background: transparent;
  color: var(--secondary-text-color);
}

.btn-text:hover {
  color: var(--primary-text-color);
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
}

/* Dark mode adjustments */
:global(.dark-mode) .info-message {
  background: rgba(33, 150, 243, 0.15);
}
</style>
