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
              <option value="light">💡 Light (LED Strip, IR Light)</option>
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
        </div>

        <!-- Step 2: Platform-Specific Configuration -->
        <div v-if="currentStep === 1" class="step-content">
          <ClimateProfileForm 
            v-if="profile.platform === 'climate'"
            v-model="profile.config"
          />
          
          <div v-else-if="profile.platform === 'media_player'" class="platform-form">
            <h3>Media Player Configuration</h3>
            <p class="help-text">
              <i class="mdi mdi-information"></i>
              Configure the features your media player supports. You'll learn the IR commands in the next step.
            </p>
            
            <div class="form-section">
              <h4>Supported Features</h4>
              <div class="checkbox-grid">
                <label class="checkbox-item">
                  <input type="checkbox" value="turn_on" v-model="mediaPlayerFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-power"></i>
                    Power On/Off
                  </span>
                </label>
                <label class="checkbox-item">
                  <input type="checkbox" value="volume" v-model="mediaPlayerFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-volume-high"></i>
                    Volume Control
                  </span>
                </label>
                <label class="checkbox-item">
                  <input type="checkbox" value="mute" v-model="mediaPlayerFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-volume-mute"></i>
                    Mute
                  </span>
                </label>
                <label class="checkbox-item">
                  <input type="checkbox" value="source" v-model="mediaPlayerFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-import"></i>
                    Source Selection
                  </span>
                </label>
                <label class="checkbox-item">
                  <input type="checkbox" value="channel" v-model="mediaPlayerFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-numeric"></i>
                    Channel Control
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div v-else-if="profile.platform === 'fan'" class="platform-form">
            <h3>Fan Configuration</h3>
            <p class="help-text">
              <i class="mdi mdi-information"></i>
              Configure the features your fan supports. You'll learn the IR commands in the next step.
            </p>
            
            <div class="form-section">
              <h4>Fan Speed Levels</h4>
              <div class="form-group">
                <label>Number of Speed Levels *</label>
                <select v-model.number="fanSpeedLevels">
                  <option :value="1">1 Speed</option>
                  <option :value="2">2 Speeds</option>
                  <option :value="3">3 Speeds (Low/Med/High)</option>
                  <option :value="4">4 Speeds</option>
                  <option :value="5">5 Speeds</option>
                  <option :value="6">6 Speeds</option>
                </select>
              </div>
            </div>
            
            <div class="form-section">
              <h4>Additional Features</h4>
              <div class="checkbox-grid">
                <label class="checkbox-item">
                  <input type="checkbox" value="oscillate" v-model="fanFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-sync"></i>
                    Oscillation
                  </span>
                </label>
                <label class="checkbox-item">
                  <input type="checkbox" value="direction" v-model="fanFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-rotate-3d-variant"></i>
                    Direction (Forward/Reverse)
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div v-else-if="profile.platform === 'light'" class="platform-form">
            <h3>Light Configuration</h3>
            <p class="help-text">
              <i class="mdi mdi-information"></i>
              Configure the features your light supports. You'll learn the IR commands in the next step.
            </p>
            
            <div class="form-section">
              <h4>Supported Features</h4>
              <div class="checkbox-grid">
                <label class="checkbox-item">
                  <input type="checkbox" value="turn_on" v-model="lightFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-power"></i>
                    Power On/Off
                  </span>
                </label>
                <label class="checkbox-item">
                  <input type="checkbox" value="brightness" v-model="lightFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-brightness-6"></i>
                    Brightness Control
                  </span>
                </label>
                <label class="checkbox-item">
                  <input type="checkbox" value="color_temp" v-model="lightFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-thermometer"></i>
                    Color Temperature
                  </span>
                </label>
                <label class="checkbox-item">
                  <input type="checkbox" value="rgb" v-model="lightFeatures" />
                  <span class="checkbox-label">
                    <i class="mdi mdi-palette"></i>
                    RGB Color
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3: Learn Commands -->
        <div v-if="currentStep === 2" class="step-content">
          <CommandLearningWizard
            v-model="profile.commands"
            :platform="profile.platform"
            :config="profile.config"
            v-model:broadlinkDevice="profile.broadlinkDevice"
            :manufacturer="profile.manufacturer"
            :model="profile.model"
            v-model:commandType="profile.commandType"
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

    <!-- Confirm Dialogs -->
    <ConfirmDialog
      :isOpen="showCommandTypeConfirm"
      title="Change Command Type?"
      message="Changing the command type will clear all learned commands. Continue?"
      confirmText="Continue"
      cancelText="Cancel"
      :dangerMode="true"
      @confirm="confirmCommandTypeChange"
      @cancel="cancelCommandTypeChange"
    />

    <ConfirmDialog
      :isOpen="showCloseConfirm"
      title="Close Profile Builder?"
      message="Are you sure you want to close? Your progress will be lost."
      confirmText="Close"
      cancelText="Keep Editing"
      :dangerMode="true"
      @confirm="confirmClose"
      @cancel="showCloseConfirm = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import ClimateProfileForm from './ClimateProfileForm.vue'
import CommandLearningWizard from './CommandLearningWizard.vue'
import ProfilePreview from './ProfilePreview.vue'
import SmartIRSetupWizard from './SmartIRSetupWizard.vue'
import ConfirmDialog from '../common/ConfirmDialog.vue'
import api from '@/services/api'

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
  },
  startStep: {
    type: Number,
    default: 0
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
const showCommandTypeConfirm = ref(false)
const showCloseConfirm = ref(false)
const pendingCommandType = ref('')
const previousCommandType = ref('ir')
const isInitialLoad = ref(false)

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

// Platform-specific feature selections
const mediaPlayerFeatures = ref(['turn_on'])
const fanSpeedLevels = ref(3)
const fanFeatures = ref([])
const lightFeatures = ref(['turn_on'])

// Watch for platform changes to update config
watch(() => profile.value.platform, (newPlatform) => {
  if (newPlatform === 'media_player') {
    profile.value.config = { features: mediaPlayerFeatures.value }
  } else if (newPlatform === 'fan') {
    profile.value.config = { speedLevels: fanSpeedLevels.value, features: fanFeatures.value }
  } else if (newPlatform === 'light') {
    profile.value.config = { features: lightFeatures.value }
  }
})

// Watch feature changes
watch(mediaPlayerFeatures, (newFeatures) => {
  if (profile.value.platform === 'media_player') {
    profile.value.config = { features: newFeatures }
  }
}, { deep: true })

watch(fanSpeedLevels, (newLevels) => {
  if (profile.value.platform === 'fan') {
    profile.value.config = { speedLevels: newLevels, features: fanFeatures.value }
  }
})

watch(fanFeatures, (newFeatures) => {
  if (profile.value.platform === 'fan') {
    profile.value.config = { speedLevels: fanSpeedLevels.value, features: newFeatures }
  }
}, { deep: true })

watch(lightFeatures, (newFeatures) => {
  if (profile.value.platform === 'light') {
    profile.value.config = { features: newFeatures }
  }
}, { deep: true })

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

// Helper function to infer media player features from commands
function inferMediaPlayerFeaturesFromCommands(commands) {
  const features = []
  const commandKeys = Object.keys(commands)
  
  if (commandKeys.some(k => k.includes('turn_on') || k.includes('turn_off') || k.includes('power'))) {
    features.push('turn_on')
  }
  if (commandKeys.some(k => k.includes('volume_up') || k.includes('volume_down') || k.includes('volume'))) {
    features.push('volume')
  }
  if (commandKeys.some(k => k.includes('mute'))) {
    features.push('mute')
  }
  if (commandKeys.some(k => k.includes('source') || k.includes('hdmi') || k.includes('input'))) {
    features.push('source')
  }
  if (commandKeys.some(k => k.includes('channel'))) {
    features.push('channel')
  }
  
  return features
}

// Helper function to infer fan features from commands
function inferFanFeaturesFromCommands(commands) {
  const features = []
  const commandKeys = Object.keys(commands)
  let maxSpeed = 0
  
  // Detect speed levels
  commandKeys.forEach(k => {
    const speedMatch = k.match(/speed[_\s]?(\d+)/i)
    if (speedMatch) {
      const speed = parseInt(speedMatch[1])
      if (speed > maxSpeed) maxSpeed = speed
    }
  })
  
  if (commandKeys.some(k => k.includes('oscillate'))) {
    features.push('oscillate')
  }
  if (commandKeys.some(k => k.includes('direction'))) {
    features.push('direction')
  }
  
  return { speedLevels: maxSpeed || 3, features }
}

// Helper function to infer light features from commands
function inferLightFeaturesFromCommands(commands) {
  const features = []
  const commandKeys = Object.keys(commands)
  
  if (commandKeys.some(k => k.includes('turn_on') || k.includes('turn_off') || k.includes('power'))) {
    features.push('turn_on')
  }
  if (commandKeys.some(k => k.includes('brightness'))) {
    features.push('brightness')
  }
  if (commandKeys.some(k => k.includes('color_temp') || k.includes('warm') || k.includes('cool'))) {
    features.push('color_temp')
  }
  if (commandKeys.some(k => k.includes('color') || k.includes('rgb') || k.includes('red') || k.includes('green') || k.includes('blue'))) {
    features.push('rgb')
  }
  
  return features
}

// Helper function to infer command type from commands
function inferCommandTypeFromCommands(commands) {
  // RF commands start with 'sc' prefix, IR commands have different preambles (e.g., '26', base64, etc.)
  // Check if any command code starts with 'sc' (RF) or is a list starting with 'sc'
  for (const commandValue of Object.values(commands)) {
    if (typeof commandValue === 'string' && commandValue.startsWith('sc')) {
      return 'rf'
    }
    if (Array.isArray(commandValue) && commandValue.length > 0 && 
        typeof commandValue[0] === 'string' && commandValue[0].startsWith('sc')) {
      return 'rf'
    }
  }
  return 'ir' // Default to IR if no 'sc' prefix found
}

// Watch for command type changes
watch(() => profile.value.commandType, (newType, oldType) => {
  // Skip if this is the initial load or if we're in the middle of a confirmation
  if (!oldType || showCommandTypeConfirm.value || isInitialLoad.value) {
    return
  }
  
  // Check if there are existing commands
  if (Object.keys(profile.value.commands).length > 0 && newType !== oldType) {
    // Store the new value and revert to old
    pendingCommandType.value = newType
    profile.value.commandType = oldType
    // Show confirmation dialog
    showCommandTypeConfirm.value = true
  } else if (newType !== oldType) {
    // No commands, just update the tracker
    previousCommandType.value = newType
  }
})

// Watch for edit data and populate profile
watch(() => props.editData, async (newData) => {
  if (newData && props.editMode) {
    console.log('🔧 Edit mode activated, loading profile data:', newData)
    
    // Set initial load flag to prevent command type change warning
    isInitialLoad.value = true
    
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
    
    // Get command type - prefer stored value, then infer from commands
    const commands = profileData.commands || {}
    const inferredCommandType = profileData.commandType || inferCommandTypeFromCommands(commands)
    
    console.log('🔍 Command type (stored):', profileData.commandType)
    console.log('🔍 Command type (final):', inferredCommandType)
    
    // Build config based on platform type
    let config = {}
    
    if (newData.platform === 'climate') {
      const inferredModes = profileData.operationModes || inferModesFromCommands(commands)
      const inferredFanModes = profileData.fanModes || inferFanModesFromCommands(commands)
      const inferredSwingModes = profileData.swingModes || inferSwingModesFromCommands(commands)
      
      console.log('🔍 Inferred modes:', inferredModes)
      console.log('🔍 Inferred fan modes:', inferredFanModes)
      console.log('🔍 Inferred swing modes:', inferredSwingModes)
      
      config = {
        minTemp: profileData.minTemperature,
        maxTemp: profileData.maxTemperature,
        precision: profileData.precision,
        modes: inferredModes,
        fanModes: inferredFanModes,
        swingModes: inferredSwingModes
      }
    } else if (newData.platform === 'media_player') {
      // Infer features from commands
      const features = []
      if (commands.on || commands.off) features.push('turn_on')
      if (commands.volumeUp || commands.volumeDown) features.push('volume')
      if (commands.mute) features.push('mute')
      if (commands.sources) features.push('source')
      if (commands.channelUp || commands.channelDown) features.push('channel')
      
      config = { features }
      mediaPlayerFeatures.value = features
      console.log('🔍 Inferred media player features:', features)
    } else if (newData.platform === 'fan') {
      // Infer speed levels from commands or speed array
      const speedLevels = profileData.speed?.length || Object.keys(commands.default || {}).length || 3
      const features = []
      if (commands.oscillate_on || commands.oscillate_off) features.push('oscillate')
      if (commands.direction_forward || commands.direction_reverse) features.push('direction')
      
      config = { speedLevels, features }
      fanSpeedLevels.value = speedLevels
      fanFeatures.value = features
      console.log('🔍 Inferred fan config:', config)
    } else if (newData.platform === 'light') {
      // Infer features from commands
      const features = []
      config = { features }
      lightFeatures.value = features
      console.log('🔍 Inferred light features:', features)
    }
    
    // Fetch learned commands from Broadlink storage to replace "pending" placeholders
    const mergedCommands = await fetchLearnedCommandsForEdit(
      profileData.manufacturer,
      profileData.supportedModels?.[0],
      commands
    )
    
    profile.value = {
      platform: newData.platform,
      manufacturer: profileData.manufacturer || '',
      model: profileData.supportedModels?.[0] || '',
      broadlinkDevice: controllerData || '',
      commandType: inferredCommandType,
      config: config,
      commands: mergedCommands
    }
    
    console.log('✅ Profile populated:', profile.value)
    console.log('✅ Selected device:', profile.value.broadlinkDevice)
    console.log('✅ Command type:', profile.value.commandType)
    console.log('✅ Commands (with learned codes):', mergedCommands)
    
    // Set the previous command type tracker
    previousCommandType.value = inferredCommandType
    
    // Clear initial load flag after a short delay to allow all watchers to settle
    setTimeout(() => {
      isInitialLoad.value = false
    }, 100)
  }
}, { immediate: true })

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return profile.value.platform && 
             profile.value.manufacturer && 
             profile.value.model
    case 1:
      // Platform-specific validation
      if (profile.value.platform === 'climate') {
        return profile.value.config.minTemp && 
               profile.value.config.maxTemp &&
               profile.value.config.modes?.length > 0
      }
      return true
    case 2:
      // Require device selection and at least some commands learned
      return profile.value.broadlinkDevice && 
             profile.value.commandType &&
             Object.keys(profile.value.commands).length > 0
    case 3:
      return true
    default:
      return false
  }
})

const generatedJson = ref(null)

async function updateGeneratedJson() {
  if (currentStep.value !== 3) {
    generatedJson.value = null
    return
  }
  
  console.log('🔍 Generating JSON with commands:', profile.value.commands)
  
  // Check if any commands are still "pending"
  const hasPending = Object.values(profile.value.commands).some(cmd => {
    if (typeof cmd === 'string') return cmd === 'pending'
    if (typeof cmd === 'object') {
      return Object.values(cmd).some(v => {
        if (typeof v === 'string') return v === 'pending'
        if (typeof v === 'object') return Object.values(v).some(vv => vv === 'pending')
        return false
      })
    }
    return false
  })
  
  if (hasPending) {
    console.warn('⚠️ Commands still contain "pending" placeholders!')
    console.log('📦 Attempting to fetch from Broadlink storage...')
    
    // Fetch learned commands from storage
    const mergedCommands = await fetchLearnedCommandsForEdit(
      profile.value.manufacturer,
      profile.value.model,
      profile.value.commands
    )
    
    profile.value.commands = mergedCommands
    console.log('✅ Updated commands:', mergedCommands)
  }
  
  generatedJson.value = generateSmartIRJson(profile.value)
  console.log('📄 Generated JSON:', generatedJson.value)
}

const generatedYaml = computed(() => {
  if (currentStep.value !== 3) return null
  
  return generateYamlConfig(profile.value)
})

function handlePlatformChange() {
  // Reset config when platform changes
  profile.value.config = {}
  profile.value.commands = {}
}

function confirmCommandTypeChange() {
  // Apply the pending change and clear commands
  showCommandTypeConfirm.value = false
  profile.value.commandType = pendingCommandType.value
  previousCommandType.value = pendingCommandType.value
  profile.value.commands = {}
  pendingCommandType.value = ''
}

function cancelCommandTypeChange() {
  // Just close the dialog, commandType is already reverted
  showCommandTypeConfirm.value = false
  pendingCommandType.value = ''
}

async function nextStep() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
    
    // If moving to preview step, fetch learned commands
    if (currentStep.value === 3) {
      await updateGeneratedJson()
    }
  }
}

function previousStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function handleOverlayClick() {
  // Don't show close confirm if another dialog is already open
  if (!showCommandTypeConfirm.value) {
    showCloseConfirm.value = true
  }
}

function confirmClose() {
  showCloseConfirm.value = false
  close()
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
      commandType: 'ir',
      config: {},
      commands: {}
    }
    previousCommandType.value = 'ir'
  }, 300)
}

async function saveToSmartIR() {
  saving.value = true
  
  try {
    // Check if setup is needed
    if (!setupCompleted.value) {
      const configCheck = await api.get('/api/smartir/config/check')
      const configStatus = configCheck.data
      if (configStatus) {
        
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
      const codeResponse = await api.get(`/api/smartir/platforms/${profile.value.platform}/next-code`)
      codeNumber = codeResponse.data.next_code
      console.log('✨ New profile: Using next code', codeNumber)
    }
    
    // Save profile to SmartIR directory
    const response = await api.post('/api/smartir/profiles', {
      platform: profile.value.platform,
      json: generatedJson.value,
      code_number: codeNumber
    })
    
    const result = response.data
    
    // Add device to configuration file
    const deviceConfig = {
      platform: 'smartir',
      name: `${profile.value.manufacturer} ${profile.value.model}`,
      unique_id: `${profile.value.manufacturer.toLowerCase().replace(/[^a-z0-9]+/g, '_')}_${profile.value.model.toLowerCase().replace(/[^a-z0-9]+/g, '_')}`,
      device_code: codeNumber,
      controller_data: profile.value.broadlinkDevice
    }
    
    try {
      await api.post('/api/smartir/config/add-device', {
        platform: profile.value.platform,
        device_config: {
          platform: 'smartir',
          name: deviceConfig.name,
          unique_id: deviceConfig.unique_id,
          device_code: deviceConfig.device_code,
          controller_data: deviceConfig.controller_data
        }
      })
    } catch (configError) {
      console.error('Failed to add device to config:', configError)
      
      // Format validation errors if available
      const errorData = configError.response?.data || {}
      let errorMessage = errorData.error || 'Unknown error'
      if (errorData.validation_errors && errorData.validation_errors.length > 0) {
        errorMessage = 'Device configuration validation failed:\n' + 
          errorData.validation_errors.map(e => `  • ${e}`).join('\n')
      }
      
      toastRef.value?.warning(
        `Profile saved but failed to add to config file:\n${errorMessage}`,
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

async function fetchLearnedCommandsForEdit(manufacturer, model, commands) {
  // Create device name from manufacturer and model (same as CommandLearningWizard)
  const mfr = manufacturer.toLowerCase().replace(/[^a-z0-9]+/g, '_')
  const mdl = model.toLowerCase().replace(/[^a-z0-9]+/g, '_')
  const deviceName = `${mfr}_${mdl}`
  
  try {
    // Fetch all Broadlink commands
    const response = await api.get('/api/commands/all')
    const data = response.data
    const deviceCommands = data[deviceName] || {}
    
    console.log(`🔍 Fetching learned commands for device: ${deviceName}`)
    console.log('📦 Device commands from storage:', deviceCommands)
    
    // Merge learned commands with profile commands
    // Replace "pending" placeholders with actual learned codes
    const mergedCommands = { ...commands }
    
    for (const [key, value] of Object.entries(mergedCommands)) {
      if (value === 'pending' && deviceCommands[key]) {
        mergedCommands[key] = deviceCommands[key]
      } else if (typeof value === 'object') {
        // Handle nested commands (climate temperature-based commands)
        for (const [tempKey, tempValue] of Object.entries(value)) {
          if (typeof tempValue === 'object') {
            for (const [fanKey, fanValue] of Object.entries(tempValue)) {
              const commandKey = `${key}_${tempKey}_${fanKey}`
              if (fanValue === 'pending' && deviceCommands[commandKey]) {
                mergedCommands[key][tempKey][fanKey] = deviceCommands[commandKey]
              }
            }
          } else if (tempValue === 'pending') {
            const commandKey = `${key}_${tempKey}`
            if (deviceCommands[commandKey]) {
              mergedCommands[key][tempKey] = deviceCommands[commandKey]
            }
          }
        }
      }
    }
    
    console.log('✅ Merged commands:', mergedCommands)
    return mergedCommands
  } catch (error) {
    console.error('Error fetching learned commands:', error)
    return commands // Return original commands if error
  }
}

function generateSmartIRJson(profile) {
  const json = {
    manufacturer: profile.manufacturer,
    supportedModels: [profile.model],
    supportedController: "Broadlink",
    commandsEncoding: "Base64",
    commandType: profile.commandType || 'ir',  // Store IR or RF type
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
    console.log('Fetching remote devices from /api/remote/devices...')
    const response = await api.get('/api/remote/devices')
    console.log('Loaded remote devices response:', response.data)
    
    // The API wraps the devices in a 'devices' property
    const devices = response.data.devices || []
    console.log('Extracted devices array:', devices)
    console.log('Device count:', devices.length)
    
    broadlinkDevices.value = devices
    console.log('broadlinkDevices.value set to:', broadlinkDevices.value)
    console.log('Final device count:', broadlinkDevices.value.length)
    if (false) {
      console.error('Response not OK:', response.status, response.statusText)
      broadlinkDevices.value = []
    }
  } catch (error) {
    console.error('Error loading remote devices:', error)
    broadlinkDevices.value = []
  }
}

watch(() => props.show, (isOpen) => {
  if (isOpen) {
    const step = Number.isInteger(props.startStep) ? props.startStep : 0
    // Clamp between 0 and steps.length - 1
    currentStep.value = Math.min(Math.max(step, 0), steps.length - 1)
  }
})

// If the desired start step changes while open, jump there
watch(() => props.startStep, (newStep) => {
  if (props.show) {
    const step = Number.isInteger(newStep) ? newStep : 0
    currentStep.value = Math.min(Math.max(step, 0), steps.length - 1)
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
  min-height: 0;
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
  flex-shrink: 0;
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

/* Platform Form Styles */
.platform-form {
  max-width: 800px;
}

.help-text {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(33, 150, 243, 0.1);
  border-left: 4px solid #2196f3;
  border-radius: 4px;
  color: var(--primary-text-color);
  margin-bottom: 24px;
  font-size: 14px;
  line-height: 1.5;
}

.help-text i {
  font-size: 20px;
  color: #2196f3;
  flex-shrink: 0;
  margin-top: 2px;
}

.form-section {
  margin-bottom: 32px;
}

.form-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-text-color);
  padding-bottom: 8px;
  border-bottom: 2px solid var(--ha-border-color);
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--ha-card-background);
  border: 2px solid var(--ha-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.checkbox-item:hover {
  border-color: var(--ha-primary-color);
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
}

.checkbox-item input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--ha-primary-color);
}

.checkbox-item input[type="checkbox"]:checked + .checkbox-label {
  color: var(--ha-primary-color);
  font-weight: 600;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--primary-text-color);
  cursor: pointer;
  user-select: none;
}

.checkbox-label i {
  font-size: 18px;
}

/* Dark mode adjustments */
:global(.dark-mode) .info-message,
:global(.dark-mode) .help-text {
  background: rgba(33, 150, 243, 0.15);
}

:global(.dark-mode) .checkbox-item {
  background: rgba(255, 255, 255, 0.05);
}

:global(.dark-mode) .checkbox-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .modal-container {
    max-height: 100vh;
    height: 100vh;
    border-radius: 0;
  }

  .modal-body {
    padding: 16px;
    padding-bottom: 80px; /* Extra padding to prevent footer overlap */
  }

  .modal-footer {
    position: sticky;
    bottom: 0;
    z-index: 10;
    padding: 12px 16px;
    background: var(--ha-card-background);
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
    flex-wrap: wrap;
    gap: 10px;
  }

  .modal-footer button {
    font-size: 13px;
    padding: 10px 14px;
  }

  /* Back button - full width on its own row */
  .modal-footer > .btn-secondary:first-child {
    order: -1;
    width: 100%;
  }

  /* Spacer - hide on mobile */
  .spacer {
    display: none;
  }

  /* Cancel and Next/Save buttons - share a row */
  .btn-text,
  .btn-primary {
    flex: 1;
  }

  /* Save buttons container - full width, stacked */
  .save-buttons {
    order: 1;
    flex-direction: column;
    width: 100%;
    gap: 8px;
  }

  .save-buttons button {
    width: 100%;
  }

  .progress-steps {
    padding: 16px 12px;
    gap: 8px;
  }

  .step {
    flex-direction: column;
    gap: 4px;
  }

  .step-label {
    font-size: 11px;
    text-align: center;
  }

  .step-number {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }

  .form-group label {
    font-size: 14px;
  }

  .form-group input,
  .form-group select {
    font-size: 14px;
  }

  .checkbox-grid {
    grid-template-columns: 1fr;
  }
}
</style>
