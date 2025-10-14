<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Learn Commands for {{ device.name }}</h2>
        <button @click="$emit('cancel')" class="close-btn">
          <i class="mdi mdi-close"></i>
        </button>
      </div>

      <form @submit.prevent="startLearning" class="modal-body">
        <!-- Broadlink Device (Read-only) -->
        <div class="form-group">
          <label for="broadlink-entity">Broadlink Device</label>
          <input
            id="broadlink-entity"
            :value="broadlinkFriendlyName"
            type="text"
            readonly
            disabled
          />
          <small>Commands will be learned using this device (set when device was created)</small>
        </div>

        <!-- Command Name Input -->
        <div class="form-group">
          <label for="command-name">Command Name *</label>
          <select
            id="command-name"
            ref="commandSelect"
            v-model="commandName"
            :disabled="learning"
            required
            @change="clearCommandValidation"
          >
            <option value="">-- Select or type command --</option>
            <optgroup label="Suggested Commands">
              <option v-for="cmd in suggestedCommands" :key="cmd" :value="cmd">
                {{ cmd }}
              </option>
            </optgroup>
            <option value="__custom__">Custom command...</option>
          </select>
          <input
            v-if="commandName === '__custom__'"
            ref="customCommandInput"
            v-model="customCommandName"
            type="text"
            placeholder="Enter custom command name"
            :disabled="learning"
            required
            class="custom-command-input"
            @input="clearCustomCommandValidation"
          />
          <small>Select a suggested command for {{ device.entity_type || 'this device' }}, or enter a custom one.</small>
        </div>

        <!-- Command Type -->
        <div class="form-group">
          <label>Command Type</label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" v-model="commandType" value="ir" :disabled="learning" />
              <span>IR (Infrared)</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="commandType" value="rf" :disabled="learning" />
              <span>RF (Radio Frequency)</span>
            </label>
          </div>
        </div>

        <!-- Learn Button (inline with inputs) -->
        <div class="learn-action">
          <button 
            type="submit"
            class="btn btn-primary btn-large" 
            :disabled="learning"
          >
            <i v-if="learning" class="mdi mdi-loading mdi-spin"></i>
            <i v-else class="mdi mdi-remote-tv"></i>
            {{ learning ? 'Learning...' : 'Learn Command' }}
          </button>
        </div>

        <!-- Learning Status -->
        <div v-if="learning" class="learning-status">
          <i class="mdi mdi-loading mdi-spin"></i>
          <p>Point your remote at the Broadlink device and press the button...</p>
          <small>This may take up to 30 seconds</small>
        </div>

        <!-- Result Message (success only for learning/deleting, errors use native validation) -->
        <!-- Test command success is shown inline on the command row -->
        <div v-if="resultMessage && resultType === 'success' && !resultMessage.includes('sent successfully')" class="result-message success">
          <i class="mdi mdi-check-circle"></i>
          <p>{{ resultMessage }}</p>
        </div>

        <!-- Section Divider -->
        <div v-if="learnedCommands.length > 0 || untrackedCommands.length > 0" class="section-divider"></div>

        <!-- Learned Commands List -->
        <div v-if="learnedCommands.length > 0" class="learned-commands">
          <h3>Tracked Commands ({{ learnedCommands.length }})</h3>
          <div class="command-list">
            <div v-for="cmd in learnedCommands" :key="cmd" class="command-item" :class="{ 'testing': testingCommand === cmd, 'tested': testedCommand === cmd }">
              <span class="command-name">{{ cmd }}</span>
              
              <!-- Inline status messages -->
              <span v-if="testingCommand === cmd" class="command-status testing">
                <i class="mdi mdi-loading mdi-spin"></i> Sending...
              </span>
              <span v-else-if="testedCommand === cmd" class="command-status success">
                <i class="mdi mdi-check-circle"></i> Sent!
              </span>
              
              <div class="command-actions">
                <button type="button" @click="testCommand(cmd)" class="icon-btn" title="Test" :disabled="testingCommand !== ''">
                  <i class="mdi mdi-play"></i>
                </button>
                <button type="button" @click="deleteCommand(cmd)" class="icon-btn danger" title="Delete" :disabled="testingCommand !== ''">
                  <i class="mdi mdi-delete"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Untracked Commands -->
        <div v-if="untrackedCommands.length > 0" class="untracked-commands">
          <h3>
            <i class="mdi mdi-alert"></i>
            Untracked Commands ({{ untrackedCommands.length }})
          </h3>
          <p class="untracked-info">
            These commands exist in Broadlink storage but are not tracked in this device.
          </p>
          <div class="command-list">
            <div v-for="cmd in untrackedCommands" :key="cmd" class="command-item untracked">
              <span class="command-name">{{ cmd }}</span>
              <span class="untracked-badge">Not tracked</span>
            </div>
          </div>
          <button type="button" @click="importUntrackedCommands" class="btn btn-secondary">
            <i class="mdi mdi-import"></i>
            Import All Untracked Commands
          </button>
        </div>
      </form>

      <div class="modal-footer">
        <button type="button" @click="$emit('cancel')" class="btn btn-secondary" :disabled="learning">
          Close
        </button>
      </div>
    </div>

    <!-- Delete Command Confirmation -->
    <ConfirmDialog
      :isOpen="showDeleteConfirm"
      :title="'Delete Command?'"
      :message="`Delete command '${commandToDelete}'? This will remove it from Broadlink storage.`"
      confirmText="Delete"
      cancelText="Cancel"
      :dangerMode="true"
      @confirm="handleDeleteConfirm"
      @cancel="cancelDeleteCommand"
    />

    <!-- Import Commands Confirmation -->
    <ConfirmDialog
      :isOpen="showImportConfirm"
      :title="'Import Commands?'"
      :message="`Import ${untrackedCommands.length} untracked command${untrackedCommands.length > 1 ? 's' : ''} into this device?`"
      confirmText="Import"
      cancelText="Cancel"
      @confirm="handleImportConfirm"
      @cancel="showImportConfirm = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '@/services/api'
import ConfirmDialog from '../common/ConfirmDialog.vue'

const props = defineProps({
  device: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['cancel', 'learned'])

const broadlinkDevices = ref([])
const selectedBroadlink = ref('')
const commandName = ref('')
const customCommandName = ref('')
const commandType = ref('ir')
const learning = ref(false)
const resultMessage = ref('')
const resultType = ref('success')
const learnedCommands = ref([])
const untrackedCommands = ref([])
const showDeleteConfirm = ref(false)
const commandToDelete = ref('')
const showImportConfirm = ref(false)
const commandSelect = ref(null)
const customCommandInput = ref(null)
const testedCommand = ref('') // Track which command was just tested
const testingCommand = ref('') // Track which command is currently being tested

const canLearn = computed(() => {
  const actualCommand = commandName.value === '__custom__' ? customCommandName.value : commandName.value
  return selectedBroadlink.value && actualCommand.trim()
})

const clearCommandValidation = () => {
  if (commandSelect.value) {
    commandSelect.value.setCustomValidity('')
  }
}

const clearCustomCommandValidation = () => {
  if (customCommandInput.value) {
    customCommandInput.value.setCustomValidity('')
  }
}

const broadlinkFriendlyName = computed(() => {
  const device = broadlinkDevices.value.find(d => d.entity_id === selectedBroadlink.value)
  return device ? (device.name || device.entity_id) : selectedBroadlink.value
})

// Command suggestions based on entity type
// Based on Home Assistant template platforms and universal media player
const ENTITY_COMMANDS = {
  light: [
    'turn_on', 'turn_off', 'toggle',
    'brightness_up', 'brightness_down',
    'dim', 'bright'
  ],
  fan: [
    'turn_on', 'turn_off', 'toggle',
    'speed_low', 'speed_medium', 'speed_high',
    'speed_1', 'speed_2', 'speed_3', 'speed_4', 'speed_5',
    'oscillate_on', 'oscillate_off',
    'direction_forward', 'direction_reverse'
  ],
  switch: [
    'turn_on', 'turn_off', 'toggle'
  ],
  media_player: [
    // Universal media player commands
    'turn_on', 'turn_off', 'toggle',
    'volume_up', 'volume_down', 'volume_mute',
    'play', 'pause', 'stop', 'play_pause',
    'next_track', 'previous_track',
    'channel_up', 'channel_down',
    'source_hdmi1', 'source_hdmi2', 'source_hdmi3',
    'source_tv', 'source_aux', 'source_bluetooth',
    'menu', 'home', 'back', 'select',
    'arrow_up', 'arrow_down', 'arrow_left', 'arrow_right'
  ],
  cover: [
    'open', 'close', 'stop',
    'open_tilt', 'close_tilt',
    'position_0', 'position_25', 'position_50', 'position_75', 'position_100'
  ]
}

const suggestedCommands = computed(() => {
  const entityType = props.device.entity_type || 'switch'
  return ENTITY_COMMANDS[entityType] || ENTITY_COMMANDS.switch
})

onMounted(async () => {
  await loadBroadlinkDevices()
  await loadLearnedCommands()
  await loadUntrackedCommands()
  
  // Set custom validation messages
  if (commandSelect.value) {
    commandSelect.value.setCustomValidity('')
    commandSelect.value.oninvalid = () => {
      commandSelect.value.setCustomValidity('Command name is required')
    }
  }
  
  // Pre-select broadlink device if set on device
  if (props.device.broadlink_entity) {
    selectedBroadlink.value = props.device.broadlink_entity
  }
})

// Watch for custom command input to appear and set validation
watch(commandName, async (newVal) => {
  if (newVal === '__custom__') {
    await nextTick()
    if (customCommandInput.value) {
      customCommandInput.value.setCustomValidity('')
      customCommandInput.value.oninvalid = () => {
        customCommandInput.value.setCustomValidity('Custom command name is required')
      }
    }
  }
})

const loadBroadlinkDevices = async () => {
  try {
    const response = await api.get('/api/broadlink/devices')
    broadlinkDevices.value = response.data.devices || []
  } catch (error) {
    console.error('Error loading Broadlink devices:', error)
  }
}

const loadLearnedCommands = async () => {
  try {
    const response = await api.get(`/api/commands/${props.device.id}`)
    const commands = response.data.commands || {}
    learnedCommands.value = Object.keys(commands)
  } catch (error) {
    console.error('Error loading commands:', error)
  }
}

const startLearning = async () => {
  // Clear previous success messages
  resultMessage.value = ''
  resultType.value = ''
  
  learning.value = true
  
  try {
    // Extract device name - try multiple sources
    let deviceName = props.device.id.split('.')[1] // Default: from entity_id
    
    // If device has a 'device' field, use that instead
    if (props.device.device) {
      deviceName = props.device.device
    }
    
    // Get the actual command name (either selected or custom)
    const actualCommand = commandName.value === '__custom__' ? customCommandName.value : commandName.value
    
    const response = await api.post('/api/commands/learn', {
      entity_id: selectedBroadlink.value,
      device: deviceName,
      command: actualCommand.trim(),
      command_type: commandType.value
    })
    
    if (response.data.success) {
      resultMessage.value = `Command "${actualCommand}" learned successfully!`
      resultType.value = 'success'
      
      // Immediately add to learned commands list (optimistic update)
      if (!learnedCommands.value.includes(actualCommand)) {
        learnedCommands.value.push(actualCommand)
      }
      
      // Remove from untracked if it was there
      const untrackedIndex = untrackedCommands.value.indexOf(actualCommand)
      if (untrackedIndex > -1) {
        untrackedCommands.value.splice(untrackedIndex, 1)
      }
      
      // Optimistically update the device's command count in the store
      // This prevents the UI from showing stale data while waiting for storage file updates
      const updatedCommands = { ...props.device.commands }
      updatedCommands[actualCommand] = true // Mark command as learned
      
      // Clear form for next command
      commandName.value = ''
      customCommandName.value = ''
      
      // Notify parent component with updated command data
      emit('learned', { commands: updatedCommands, commandName: actualCommand })
    } else {
      resultMessage.value = response.data.error || 'Failed to learn command'
      resultType.value = 'error'
    }
  } catch (error) {
    resultMessage.value = error.response?.data?.error || 'Error learning command'
    resultType.value = 'error'
  } finally {
    learning.value = false
  }
}

const testCommand = async (command) => {
  try {
    // Set testing state
    testingCommand.value = command
    testedCommand.value = '' // Clear previous tested state
    
    // Extract device name - try multiple sources
    let deviceName = props.device.id.split('.')[1]
    if (props.device.device) {
      deviceName = props.device.device
    }
    
    const response = await api.post('/api/commands/test', {
      entity_id: selectedBroadlink.value,
      device: deviceName,
      command: command,
      device_id: props.device.id
    })
    
    if (response.data.success) {
      // Show success on the command row
      testedCommand.value = command
      
      // Auto-clear after 2 seconds
      setTimeout(() => {
        if (testedCommand.value === command) {
          testedCommand.value = ''
        }
      }, 2000)
    }
  } catch (error) {
    resultMessage.value = `Failed to send command: ${error.message}`
    resultType.value = 'error'
  } finally {
    testingCommand.value = ''
  }
}

const deleteCommand = (command) => {
  commandToDelete.value = command
  showDeleteConfirm.value = true
}

const cancelDeleteCommand = () => {
  showDeleteConfirm.value = false
  commandToDelete.value = ''
}

const handleDeleteConfirm = async () => {
  const command = commandToDelete.value
  showDeleteConfirm.value = false
  
  try {
    await api.delete(`/api/commands/${props.device.id}/${command}`)
    await loadLearnedCommands()
    await loadUntrackedCommands()
    resultMessage.value = `Command "${command}" deleted`
    resultType.value = 'success'
    emit('learned')
  } catch (error) {
    resultMessage.value = `Failed to delete command: ${error.message}`
    resultType.value = 'error'
  } finally {
    commandToDelete.value = ''
  }
}

const loadUntrackedCommands = async () => {
  try {
    // Get device name from device object
    const deviceName = props.device.device || props.device.id.split('.')[1]
    
    // Get all untracked commands
    const response = await api.get('/api/commands/untracked')
    const untracked = response.data.untracked || {}
    
    // Get untracked commands for this device
    if (untracked[deviceName]) {
      untrackedCommands.value = Object.keys(untracked[deviceName].commands)
    } else {
      untrackedCommands.value = []
    }
  } catch (error) {
    console.error('Error loading untracked commands:', error)
    untrackedCommands.value = []
  }
}

const importUntrackedCommands = () => {
  if (untrackedCommands.value.length === 0) return
  showImportConfirm.value = true
}

const handleImportConfirm = async () => {
  showImportConfirm.value = false
  
  try {
    const deviceName = props.device.device || props.device.id.split('.')[1]
    
    const response = await api.post('/api/commands/import', {
      device_id: props.device.id,
      source_device: deviceName,
      commands: untrackedCommands.value
    })
    
    if (response.data.success) {
      resultMessage.value = `Imported ${response.data.imported_count} commands successfully!`
      resultType.value = 'success'
      
      // Reload commands
      await loadLearnedCommands()
      await loadUntrackedCommands()
      emit('learned')
    }
  } catch (error) {
    resultMessage.value = `Failed to import commands: ${error.message}`
    resultType.value = 'error'
  }
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
  max-width: 700px;
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

.radio-group {
  display: flex;
  gap: 16px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio-label input[type="radio"] {
  width: auto;
  cursor: pointer;
}

.learning-status {
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1);
  border: 1px solid var(--ha-primary-color);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  margin: 20px 0;
}

.learning-status i {
  font-size: 48px;
  color: var(--ha-primary-color);
  margin-bottom: 12px;
}

.learning-status p {
  margin: 0 0 8px 0;
  color: var(--ha-text-primary-color);
  font-weight: 500;
}

.learning-status small {
  color: var(--ha-text-secondary-color);
}

.result-message {
  padding: 16px;
  border-radius: 8px;
  margin: 16px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-message.success {
  background: rgba(var(--ha-success-rgb), 0.1);
  border: 1px solid var(--ha-success-color);
  color: var(--ha-success-color);
}

.result-message.error {
  background: rgba(var(--ha-error-rgb), 0.1);
  border: 1px solid var(--ha-error-color);
  color: var(--ha-error-color);
}

.result-message i {
  font-size: 24px;
}

.result-message p {
  margin: 0;
  flex: 1;
}

.learned-commands,
.untracked-commands {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--ha-border-color);
}

.learned-commands h3,
.untracked-commands h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: var(--ha-text-primary-color);
  display: flex;
  align-items: center;
  gap: 8px;
}

.untracked-commands h3 i {
  color: var(--ha-warning-color, #ff9800);
}

.untracked-info {
  margin: 0 0 16px 0;
  padding: 12px;
  background: rgba(var(--ha-warning-rgb, 255, 152, 0), 0.1);
  border-left: 3px solid var(--ha-warning-color, #ff9800);
  border-radius: 4px;
  font-size: 14px;
  color: var(--ha-text-secondary-color);
}

.command-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.command-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--ha-surface-color);
  border-radius: 8px;
  border: 1px solid var(--ha-border-color);
}

.command-name {
  font-family: monospace;
  color: var(--ha-text-primary-color);
  font-weight: 500;
}

.untracked-badge {
  padding: 4px 8px;
  background: rgba(var(--ha-warning-rgb, 255, 152, 0), 0.2);
  color: var(--ha-warning-color, #ff9800);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.command-item.untracked {
  background: rgba(var(--ha-warning-rgb, 255, 152, 0), 0.05);
  border-color: var(--ha-warning-color, #ff9800);
}

.command-item.testing {
  background: rgba(3, 169, 244, 0.08);
  border-color: #03a9f4;
}

.command-item.tested {
  background: rgba(76, 175, 80, 0.08);
  border-color: #4caf50;
}

.command-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  margin-left: auto;
  margin-right: 8px;
}

.command-status.testing {
  background: rgba(3, 169, 244, 0.15);
  color: #03a9f4;
}

.command-status.success {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.command-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  background: transparent;
  border: 1px solid var(--ha-border-color);
  color: var(--ha-text-primary-color);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.icon-btn:hover {
  background: var(--ha-hover-color);
  border-color: var(--ha-primary-color);
}

.icon-btn.danger:hover {
  background: rgba(var(--ha-error-rgb), 0.1);
  border-color: var(--ha-error-color);
  color: var(--ha-error-color);
}

.custom-command-input {
  margin-top: 8px;
  padding: 10px 12px;
  background: var(--ha-surface-color);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  width: 100%;
}

.custom-command-input:focus {
  outline: none;
  border-color: var(--ha-primary-color);
}

.learn-action {
  margin-top: 8px;
  margin-bottom: 16px;
}

.btn-large {
  width: 100%;
  padding: 14px 24px;
  font-size: 16px;
  font-weight: 600;
}

.section-divider {
  height: 1px;
  background: var(--ha-border-color);
  margin: 24px 0;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 24px;
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
