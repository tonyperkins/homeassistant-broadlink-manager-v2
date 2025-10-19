<template>
  <div class="command-wizard">
    <h3>Learn IR Commands</h3>
    
    <!-- Device Selection -->
    <div class="device-selection-section">
      <div class="form-group" :class="{ 'has-error': showDeviceError }">
        <label>Broadlink Device *</label>
        <div class="input-wrapper">
          <select v-model="localBroadlinkDevice" @change="updateBroadlinkDevice">
            <option value="">Select Broadlink device...</option>
            <option 
              v-for="device in broadlinkDevices" 
              :key="device.entity_id"
              :value="device.entity_id"
            >
              {{ device.name }}{{ device.area_name ? ' (' + device.area_name + ')' : '' }}
            </option>
          </select>
          <div v-if="showDeviceError" class="validation-tooltip">
            <i class="mdi mdi-alert"></i>
            Device is required
          </div>
        </div>
        <small>This device will be used to learn commands ({{ broadlinkDevices.length }} devices found)</small>
      </div>

      <div class="form-group">
        <label>Command Type *</label>
        <select v-model="localCommandType" @change="updateCommandType" :disabled="learnedCount > 0">
          <option value="ir">📡 Infrared (IR) - Most common for AC, TV, etc.</option>
          <option value="rf">📻 Radio Frequency (RF) - For RF remotes</option>
        </select>
        <small v-if="learnedCount > 0">Command type cannot be changed after learning commands</small>
        <small v-else>Select the type of commands your device uses</small>
      </div>
    </div>
    
    <!-- Edit Mode Banner -->
    <div v-if="learnedCount > 0 && !hasLearnedAny" class="edit-mode-banner">
      <i class="mdi mdi-information-outline"></i>
      <div>
        <strong>Editing Existing Profile</strong>
        <p>{{ learnedCount }} command{{ learnedCount !== 1 ? 's' : '' }} already learned. You can re-learn any command by clicking the delete icon and then "Learn Command".</p>
      </div>
    </div>
    
    <div class="wizard-info">
      <i class="mdi mdi-information"></i>
      <div>
        <p><strong>How it works:</strong></p>
        <ol v-if="commandType === 'ir'">
          <li>Click "Learn Command" for each combination</li>
          <li><strong>Point your IR remote directly at the Broadlink device</strong></li>
          <li>Press the button on your remote</li>
          <li>Wait for confirmation (up to 30 seconds)</li>
        </ol>
        <ol v-else>
          <li>Click "Learn Command" for each combination</li>
          <li><strong>Step 1:</strong> Hold button on remote - Broadlink scans for RF frequency</li>
          <li><strong>Step 2:</strong> Watch for Home Assistant notification, then press and release button</li>
          <li>Keep remote within 5cm of Broadlink (RF doesn't need line-of-sight)</li>
          <li>Wait for confirmation (may take up to 30 seconds)</li>
        </ol>
      </div>
    </div>

    <div class="progress-info">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
      </div>
      <span class="progress-text">
        {{ learnedCount }} / {{ totalCommands }} commands learned ({{ progressPercentage }}%)
      </span>
    </div>

    <!-- Command Learning Grid -->
    <div class="commands-grid">
      <div 
        v-for="cmd in commandList" 
        :key="cmd.key"
        class="command-card"
        :class="{
          'learned': commands[cmd.key],
          'learning': learningCommand === cmd.key
        }"
      >
        <div class="command-header">
          <div class="command-icon">
            <i :class="cmd.icon"></i>
          </div>
          <div class="command-info">
            <h4>{{ cmd.label }}</h4>
            <p>{{ cmd.description }}</p>
          </div>
        </div>

        <!-- Learning Instructions (shown above button when learning) -->
        <div v-if="learningCommand === cmd.key" class="learning-indicator">
          <div v-if="commandType === 'ir'" class="ir-learning-steps">
            <p><strong>Point your remote directly at the Broadlink device and press the button.</strong></p>
            <small>Listening for up to 30 seconds...</small>
          </div>
          <div v-else class="rf-learning-steps">
            <p class="rf-title"><strong>Learning request sent to device.</strong></p>
            <p class="rf-subtitle">RF learning is a <strong>two-step process</strong>:</p>
            <ol>
              <li>
                <strong>Step 1 - Frequency Sweep (~10-15 seconds):</strong> Press and hold the button on your remote until the notification updates.
              </li>
              <li>
                <strong>Step 2 - Learn Signal:</strong> Press and release the button once.
              </li>
            </ol>
            <p class="rf-note">Follow the Home Assistant notifications (🔔) for real-time instructions.</p>
          </div>
        </div>

        <div class="command-actions">
          <button 
            v-if="!commands[cmd.key]"
            @click="learnCommand(cmd)"
            class="btn-learn"
            :class="{ 'learning': learningCommand === cmd.key }"
            :disabled="learningCommand !== null"
          >
            <i class="mdi mdi-radio-tower" :class="{ 'mdi-spin': learningCommand === cmd.key }"></i>
            {{ learningCommand === cmd.key ? 'Listening...' : 'Learn Command' }}
          </button>
          
          <div v-else class="learned-status">
            <i class="mdi mdi-check-circle"></i>
            <span>Learned</span>
            <span class="command-type-badge" :class="localCommandType">
              {{ localCommandType.toUpperCase() }}
            </span>
            <button @click="testCommand(cmd.key)" class="icon-btn" title="Test command" :disabled="testingCommand === cmd.key" style="margin-left:auto">
              <i class="mdi mdi-play" :class="{ 'mdi-spin': testingCommand === cmd.key }"></i>
            </button>
            <button @click="deleteCommand(cmd.key)" class="icon-btn danger" title="Delete and re-learn" >
              <i class="mdi mdi-delete"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <button 
        @click="learnAllSequentially" 
        class="btn-secondary"
        :disabled="learningCommand !== null || learnedCount === totalCommands"
      >
        <i class="mdi mdi-play-circle"></i>
        Learn All Remaining
      </button>
      
      <button 
        @click="clearAll" 
        class="btn-text"
        :disabled="learnedCount === 0"
      >
        <i class="mdi mdi-delete-sweep"></i>
        Clear All
      </button>
    </div>

    <!-- Confirm Delete Dialog -->
    <ConfirmDialog
      :isOpen="confirmDelete.show"
      title="Delete Learned Command?"
      :message="`Are you sure you want to delete the '${confirmDelete.commandLabel}' command?\n\nYou will need to re-learn this command.`"
      confirmText="Delete"
      cancelText="Cancel"
      :dangerMode="true"
      @confirm="handleDeleteConfirm"
      @cancel="confirmDelete.show = false"
    />

    <!-- Confirm Clear All Dialog -->
    <ConfirmDialog
      :isOpen="confirmClearAll"
      title="Delete All Learned Commands?"
      message="Are you sure you want to delete all learned commands? This cannot be undone.\n\nYou will need to re-learn all commands."
      confirmText="Delete All"
      cancelText="Cancel"
      :dangerMode="true"
      @confirm="handleClearAllConfirm"
      @cancel="confirmClearAll = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import ConfirmDialog from '../common/ConfirmDialog.vue'

const toast = useToast()

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  platform: {
    type: String,
    required: true
  },
  config: {
    type: Object,
    required: true
  },
  broadlinkDevice: {
    type: String,
    default: ''
  },
  manufacturer: {
    type: String,
    required: true
  },
  model: {
    type: String,
    required: true
  },
  commandType: {
    type: String,
    default: 'ir'
  }
})

const emit = defineEmits(['update:modelValue', 'update:broadlinkDevice', 'update:commandType'])

const commands = ref({ ...props.modelValue })
const learningCommand = ref(null)
const testingCommand = ref(null)
const broadlinkDevices = ref([])
const localBroadlinkDevice = ref(props.broadlinkDevice)
const localCommandType = ref(props.commandType)
const sequentialLearning = ref(false)
const sequentialQueue = ref([])
const hasLearnedAny = ref(false) // Track if user has learned any commands in this session
const showDeviceError = ref(false) // Track validation error for Broadlink device
const confirmDelete = ref({
  show: false,
  commandKey: null,
  commandLabel: ''
})
const confirmClearAll = ref(false)

const commandList = computed(() => {
  const list = []
  
  if (props.platform === 'climate') {
    const modes = props.config.modes || []
    const fanModes = props.config.fanModes || []
    const minTemp = props.config.minTemp || 16
    const maxTemp = props.config.maxTemp || 30
    
    // Generate commands for each mode/temp/fan combination
    modes.forEach(mode => {
      if (mode === 'off') {
        list.push({
          key: 'off',
          label: 'Power Off',
          description: 'Turn device off',
          icon: 'mdi mdi-power',
          mode: 'off'
        })
      } else {
        // For each temperature
        for (let temp = minTemp; temp <= maxTemp; temp++) {
          fanModes.forEach(fanMode => {
            const key = `${mode}_${temp}_${fanMode}`
            list.push({
              key,
              label: `${mode.toUpperCase()} ${temp}°C ${fanMode}`,
              description: `Mode: ${mode}, Temp: ${temp}°C, Fan: ${fanMode}`,
              icon: getModeIcon(mode),
              mode,
              temp,
              fanMode
            })
          })
        }
      }
    })
  } else if (props.platform === 'media_player') {
    const features = props.config.features || []
    
    if (features.includes('turn_on')) {
      list.push({ key: 'turn_on', label: 'Power On', description: 'Turn on the device', icon: 'mdi mdi-power' })
      list.push({ key: 'turn_off', label: 'Power Off', description: 'Turn off the device', icon: 'mdi mdi-power-off' })
    }
    if (features.includes('volume')) {
      list.push({ key: 'volume_up', label: 'Volume Up', description: 'Increase volume', icon: 'mdi mdi-volume-plus' })
      list.push({ key: 'volume_down', label: 'Volume Down', description: 'Decrease volume', icon: 'mdi mdi-volume-minus' })
    }
    if (features.includes('mute')) {
      list.push({ key: 'mute', label: 'Mute', description: 'Toggle mute', icon: 'mdi mdi-volume-mute' })
    }
    if (features.includes('source')) {
      list.push({ key: 'source_hdmi1', label: 'Source: HDMI 1', description: 'Switch to HDMI 1', icon: 'mdi mdi-import' })
      list.push({ key: 'source_hdmi2', label: 'Source: HDMI 2', description: 'Switch to HDMI 2', icon: 'mdi mdi-import' })
      list.push({ key: 'source_hdmi3', label: 'Source: HDMI 3', description: 'Switch to HDMI 3', icon: 'mdi mdi-import' })
    }
    if (features.includes('channel')) {
      list.push({ key: 'channel_up', label: 'Channel Up', description: 'Next channel', icon: 'mdi mdi-chevron-up' })
      list.push({ key: 'channel_down', label: 'Channel Down', description: 'Previous channel', icon: 'mdi mdi-chevron-down' })
    }
  } else if (props.platform === 'fan') {
    const speedLevels = props.config.speedLevels || 3
    const features = props.config.features || []
    
    list.push({ key: 'turn_on', label: 'Power On', description: 'Turn on the fan', icon: 'mdi mdi-power' })
    list.push({ key: 'turn_off', label: 'Power Off', description: 'Turn off the fan', icon: 'mdi mdi-power-off' })
    
    for (let i = 1; i <= speedLevels; i++) {
      const speedName = i === 1 ? 'Low' : i === speedLevels ? 'High' : i === 2 && speedLevels === 3 ? 'Medium' : `Speed ${i}`
      list.push({ 
        key: `speed_${i}`, 
        label: `${speedName}`, 
        description: `Set fan to speed level ${i}`, 
        icon: 'mdi mdi-fan' 
      })
    }
    
    if (features.includes('oscillate')) {
      list.push({ key: 'oscillate_on', label: 'Oscillate On', description: 'Enable oscillation', icon: 'mdi mdi-sync' })
      list.push({ key: 'oscillate_off', label: 'Oscillate Off', description: 'Disable oscillation', icon: 'mdi mdi-sync-off' })
    }
    if (features.includes('direction')) {
      list.push({ key: 'direction_forward', label: 'Direction: Forward', description: 'Set direction to forward', icon: 'mdi mdi-rotate-right' })
      list.push({ key: 'direction_reverse', label: 'Direction: Reverse', description: 'Set direction to reverse', icon: 'mdi mdi-rotate-left' })
    }
  } else if (props.platform === 'light') {
    const features = props.config.features || []
    
    if (features.includes('turn_on')) {
      list.push({ key: 'turn_on', label: 'Power On', description: 'Turn on the light', icon: 'mdi mdi-lightbulb-on' })
      list.push({ key: 'turn_off', label: 'Power Off', description: 'Turn off the light', icon: 'mdi mdi-lightbulb-off' })
    }
    if (features.includes('brightness')) {
      list.push({ key: 'brightness_up', label: 'Brightness Up', description: 'Increase brightness', icon: 'mdi mdi-brightness-7' })
      list.push({ key: 'brightness_down', label: 'Brightness Down', description: 'Decrease brightness', icon: 'mdi mdi-brightness-5' })
    }
    if (features.includes('color_temp')) {
      list.push({ key: 'color_temp_warm', label: 'Warm White', description: 'Set to warm white', icon: 'mdi mdi-weather-sunset' })
      list.push({ key: 'color_temp_cool', label: 'Cool White', description: 'Set to cool white', icon: 'mdi mdi-weather-sunny' })
    }
    if (features.includes('rgb')) {
      list.push({ key: 'color_red', label: 'Color: Red', description: 'Set color to red', icon: 'mdi mdi-palette' })
      list.push({ key: 'color_green', label: 'Color: Green', description: 'Set color to green', icon: 'mdi mdi-palette' })
      list.push({ key: 'color_blue', label: 'Color: Blue', description: 'Set color to blue', icon: 'mdi mdi-palette' })
    }
  }
  
  return list
})

const totalCommands = computed(() => commandList.value.length)
const learnedCount = computed(() => Object.keys(commands.value).length)
const progressPercentage = computed(() => {
  if (totalCommands.value === 0) return 0
  return Math.round((learnedCount.value / totalCommands.value) * 100)
})

function getModeIcon(mode) {
  const icons = {
    'off': 'mdi mdi-power',
    'auto': 'mdi mdi-autorenew',
    'cool': 'mdi mdi-snowflake',
    'heat': 'mdi mdi-fire',
    'dry': 'mdi mdi-water-percent',
    'fan_only': 'mdi mdi-fan'
  }
  return icons[mode] || 'mdi mdi-remote'
}

async function learnCommand(cmd) {
  if (learningCommand.value) return

  // Validate that a Broadlink device is selected
  if (!localBroadlinkDevice.value) {
    showDeviceError.value = true
    // Scroll to top to show the error
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }
  
  // Clear error if device is selected
  showDeviceError.value = false
  
  learningCommand.value = cmd.key
  
  try {
    // Create device name from manufacturer and model (e.g., "daikin_ftxs35k")
    const manufacturer = props.manufacturer.toLowerCase().replace(/[^a-z0-9]+/g, '_')
    const model = props.model.toLowerCase().replace(/[^a-z0-9]+/g, '_')
    const deviceName = `${manufacturer}_${model}`
    
    // Call the learn command API
    const response = await fetch('/api/commands/learn', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        entity_id: localBroadlinkDevice.value,
        device: deviceName,
        command: cmd.key,
        command_type: localCommandType.value // Use the selected command type (ir or rf)
      })
    })
    
    if (!response.ok) {
      throw new Error(`Failed to learn command: ${response.statusText}`)
    }
    
    const result = await response.json()
    
    if (result.success && result.code) {
      // Store the command code (or placeholder for pending)
      commands.value[cmd.key] = result.code
      emit('update:modelValue', commands.value)
      hasLearnedAny.value = true // Mark that user has learned at least one command
      
      if (result.code === 'pending') {
        // Code is pending - it will be fetched when saving the profile
        console.log(`⏳ Command '${cmd.key}' learned, code will be fetched from storage when saving`)
      }
      
      // If sequential learning, move to next
      if (sequentialLearning.value && sequentialQueue.value.length > 0) {
        setTimeout(() => {
          const nextCmd = sequentialQueue.value.shift()
          if (nextCmd) {
            learnCommand(nextCmd)
          } else {
            sequentialLearning.value = false
          }
        }, 1000)
      }
    } else {
      throw new Error(result.error || 'Failed to learn command')
    }
  } catch (error) {
    console.error('Error learning command:', error)
    toast.error(`Error learning command: ${error.message}`)
    sequentialLearning.value = false
    sequentialQueue.value = []
  } finally {
    if (!sequentialLearning.value) {
      learningCommand.value = null
    }
  }
}

async function testCommand(key) {
  if (!localBroadlinkDevice.value) {
    showDeviceError.value = true
    // Scroll to top to show the error
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }
  
  if (!commands.value[key]) {
    toast.value?.error('Command not learned yet')
    return
  }
  
  testingCommand.value = key
  
  try {
    // Get the raw IR/RF code from memory (should be the actual code, not "pending")
    const rawCode = commands.value[key]
    
    // Send raw code using dedicated endpoint
    const response = await fetch('/api/commands/send-raw', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entity_id: localBroadlinkDevice.value,
        command: rawCode,  // Send the base64 IR/RF code directly
        command_type: localCommandType.value  // 'ir' or 'rf'
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to send command')
    }
    
    toast.success('Command sent successfully')
  } catch (error) {
    console.error('Error testing command:', error)
    toast.error(`Error testing command: ${error.message}`)
  } finally {
    testingCommand.value = null
  }
}

function deleteCommand(key) {
  // Find the command label for the confirmation message
  const cmd = commandList.value.find(c => c.key === key)
  confirmDelete.value = {
    show: true,
    commandKey: key,
    commandLabel: cmd ? cmd.label : key
  }
}

function handleDeleteConfirm() {
  const key = confirmDelete.value.commandKey
  delete commands.value[key]
  emit('update:modelValue', commands.value)
  confirmDelete.value.show = false
}

function learnAllSequentially() {
  const unlearned = commandList.value.filter(cmd => !commands.value[cmd.key])
  
  if (unlearned.length === 0) {
    // All commands already learned, nothing to do
    return
  }
  
  // Start sequential learning immediately
  sequentialLearning.value = true
  sequentialQueue.value = [...unlearned]
  const firstCmd = sequentialQueue.value.shift()
  if (firstCmd) {
    learnCommand(firstCmd)
  }
}

function clearAll() {
  confirmClearAll.value = true
}

function handleClearAllConfirm() {
  commands.value = {}
  emit('update:modelValue', commands.value)
  confirmClearAll.value = false
}

watch(() => props.modelValue, (newValue) => {
  commands.value = { ...newValue }
}, { deep: true })

// Load existing commands from Broadlink storage when component mounts
onMounted(async () => {
  await loadExistingCommands()
})

async function loadExistingCommands() {
  try {
    // For SmartIR devices, we load commands from the SmartIR JSON file, NOT Broadlink storage
    // SmartIR devices store their commands in JSON files in custom_components/smartir/codes/
    // We should only load commands that have actual IR codes (not "pending")
    
    // Note: This function is intentionally left empty for SmartIR devices
    // SmartIR commands are managed through the SmartIR JSON files, not Broadlink storage
    // The wizard will start with empty commands and users learn them one by one
    
    console.log('SmartIR device - commands will be loaded from SmartIR JSON file, not Broadlink storage')
  } catch (error) {
    console.error('Error in loadExistingCommands:', error)
  }
}

function updateBroadlinkDevice() {
  emit('update:broadlinkDevice', localBroadlinkDevice.value)
}

function updateCommandType() {
  emit('update:commandType', localCommandType.value)
}

async function loadBroadlinkDevices() {
  try {
    const response = await fetch('/api/remote/devices')
    if (response.ok) {
      const data = await response.json()
      const devices = data.devices || []
      broadlinkDevices.value = devices
    }
  } catch (error) {
    console.error('Error loading remote devices:', error)
    broadlinkDevices.value = []
  }
}

// Watch for prop changes and update local refs
watch(() => props.broadlinkDevice, (newVal) => {
  localBroadlinkDevice.value = newVal
})

// Clear validation error when device is selected
watch(localBroadlinkDevice, (newVal) => {
  if (newVal) {
    showDeviceError.value = false
  }
})

watch(() => props.commandType, (newVal) => {
  localCommandType.value = newVal
})

// Load devices on mount
onMounted(async () => {
  await loadBroadlinkDevices()
  // Also try to load existing commands
  await loadExistingCommands()
})
</script>

<style scoped>
.command-wizard h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.device-selection-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.05);
  border-radius: 8px;
  border: 1px solid var(--ha-border-color);
}

.device-selection-section .form-group {
  margin: 0;
}

.device-selection-section label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--ha-text-primary-color);
}

.device-selection-section select {
  width: 100%;
  padding: 10px 12px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 6px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.device-selection-section select:hover {
  border-color: var(--ha-primary-color);
}

.device-selection-section select:focus {
  outline: none;
  border-color: var(--ha-primary-color);
  box-shadow: 0 0 0 3px rgba(var(--ha-primary-rgb), 0.1);
}

.device-selection-section small {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--ha-text-secondary-color);
}

.edit-mode-banner {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: rgba(76, 175, 80, 0.1);
  border-radius: 8px;
  border-left: 4px solid #4caf50;
  margin-bottom: 16px;
}

.edit-mode-banner i {
  font-size: 24px;
  color: #4caf50;
  flex-shrink: 0;
}

.edit-mode-banner strong {
  display: block;
  margin-bottom: 4px;
  color: var(--primary-text-color);
  font-size: 15px;
}

.edit-mode-banner p {
  margin: 0;
  color: var(--secondary-text-color);
  font-size: 14px;
  line-height: 1.5;
}

.wizard-info {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: rgba(33, 150, 243, 0.1);
  border-radius: 8px;
  border-left: 4px solid #2196f3;
  margin-bottom: 24px;
}

.wizard-info i {
  font-size: 24px;
  color: #2196f3;
  flex-shrink: 0;
}

.wizard-info p {
  margin: 0 0 8px 0;
  color: var(--primary-text-color);
  font-weight: 600;
}

.wizard-info ol {
  margin: 0;
  padding-left: 20px;
  color: var(--primary-text-color);
}

.wizard-info li {
  margin-bottom: 4px;
  font-size: 14px;
}

.progress-info {
  margin-bottom: 24px;
}

.progress-bar {
  height: 8px;
  background: var(--ha-border-color);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), #4caf50);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: var(--secondary-text-color);
  font-weight: 600;
}

.commands-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  max-height: 400px;
  overflow-y: auto;
  padding: 4px;
}

.command-card {
  background: var(--ha-card-background);
  border: 2px solid var(--ha-border-color);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.command-card.learned {
  border-color: #4caf50;
  background: rgba(76, 175, 80, 0.05);
}

.command-card.learning {
  border-color: var(--primary-color);
  background: rgba(var(--primary-color-rgb, 3, 169, 244), 0.05);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(var(--primary-color-rgb, 3, 169, 244), 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(var(--primary-color-rgb, 3, 169, 244), 0);
  }
}

.command-header {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.command-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 8px;
  flex-shrink: 0;
}

.command-icon i {
  font-size: 20px;
}

.command-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.command-info p {
  margin: 0;
  font-size: 12px;
  color: var(--secondary-text-color);
}

.command-actions {
  margin-top: 12px;
}

.btn-learn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  background: var(--ha-primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-learn:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-learn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-learn.learning {
  padding: 8px 16px;
  font-size: 13px;
}

.learned-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: rgba(76, 175, 80, 0.1);
  border-radius: 6px;
  color: #4caf50;
  font-weight: 600;
  font-size: 14px;
}

.learned-status i {
  font-size: 20px;
}

.command-type-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.command-type-badge.ir {
  background: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.command-type-badge.rf {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.icon-btn {
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  color: var(--ha-text-primary-color);
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover:not(:disabled) {
  background: var(--ha-primary-color);
  border-color: var(--ha-primary-color);
  color: white;
}

.icon-btn.danger:hover:not(:disabled) {
  background: var(--ha-error-color);
  border-color: var(--ha-error-color);
  color: white;
}

.icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.learning-indicator {
  margin-bottom: 12px;
  padding: 12px;
  background: rgba(var(--primary-color-rgb, 3, 169, 244), 0.1);
  border-radius: 8px;
  border-left: 4px solid rgb(var(--primary-color-rgb, 3, 169, 244));
  text-align: left;
}

.pulse-ring {
  width: 40px;
  height: 40px;
  margin: 0 auto 8px;
  border: 3px solid var(--primary-color);
  border-radius: 50%;
  animation: pulseRing 1.5s infinite;
}

@keyframes pulseRing {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.5;
  }
  100% {
    transform: scale(0.8);
    opacity: 1;
  }
}

.learning-indicator p {
  margin: 0;
  font-size: 13px;
  color: var(--primary-text-color);
}

.ir-learning-steps p {
  margin: 0 0 6px 0;
  font-size: 13px;
  line-height: 1.5;
}

.ir-learning-steps small {
  font-size: 12px;
  color: var(--secondary-text-color);
}

.rf-learning-steps {
  text-align: left;
}

.rf-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--primary-text-color);
}

.rf-subtitle {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: var(--primary-text-color);
}

.rf-learning-steps ol {
  margin: 0 0 12px 0;
  padding-left: 20px;
  font-size: 13px;
  line-height: 1.7;
}

.rf-learning-steps li {
  margin-bottom: 10px;
}

.rf-note {
  margin: 12px 0 0 0;
  padding: 10px 12px;
  background: rgba(255, 193, 7, 0.15);
  border-left: 3px solid #ffc107;
  border-radius: 4px;
  font-size: 12px;
  color: var(--primary-text-color);
}

.quick-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--ha-border-color);
}

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

.btn-secondary {
  background: transparent;
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--primary-color);
  color: white;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-text {
  background: transparent;
  color: var(--secondary-text-color);
}

.btn-text:hover:not(:disabled) {
  color: #f44336;
  background: rgba(244, 67, 54, 0.1);
}

.btn-text:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Validation tooltip styling */
.input-wrapper {
  position: relative;
}

.form-group.has-error select {
  border-color: #ff9800;
}

.validation-tooltip {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
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
  left: 20px;
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-bottom: 8px solid white;
  filter: drop-shadow(0 -2px 2px rgba(0, 0, 0, 0.05));
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

/* Dark mode adjustments */
:global(.dark-mode) .validation-tooltip {
  background: #2d2d2d;
  border-color: #444;
  color: #e0e0e0;
}

:global(.dark-mode) .validation-tooltip::before {
  border-bottom-color: #2d2d2d;
}

:global(.dark-mode) .wizard-info {
  background: rgba(33, 150, 243, 0.15);
}

:global(.dark-mode) .command-card.learned {
  background: rgba(76, 175, 80, 0.1);
}

:global(.dark-mode) .command-card.learning {
  background: rgba(var(--primary-color-rgb, 3, 169, 244), 0.1);
}
</style>
