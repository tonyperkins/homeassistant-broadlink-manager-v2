<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ isSmartIR ? 'Commands for' : 'Learn Commands for' }} {{ device.name }}</h2>
        <button @click="$emit('cancel')" class="close-btn">
          <i class="mdi mdi-close"></i>
        </button>
      </div>

      <div class="modal-body">
        <!-- SmartIR Info Message -->
        <div v-if="isSmartIR" class="smartir-info">
          <i class="mdi mdi-information"></i>
          <div>
            <h3>SmartIR Device</h3>
            <p>This device uses SmartIR code file <strong>{{ device.device_code }}</strong>. Commands are pre-configured and cannot be learned.</p>
            <p v-if="device.entity_type === 'climate'" class="climate-note">
              <i class="mdi mdi-alert-circle-outline"></i>
              <strong>Note:</strong> Climate device commands are temperature-based. Testing individual modes may not work as expected. Use the Home Assistant climate card to control your device.
            </p>
          </div>
        </div>

        <form v-else @submit.prevent="startLearning">
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

        <!-- Save Destination -->
        <div class="form-group">
          <label>
            Save Destination
            <button type="button" class="help-btn" @click="showSaveDestinationHelp = !showSaveDestinationHelp" title="Learn more">
              <i class="mdi mdi-help-circle-outline"></i>
            </button>
          </label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" v-model="saveDestination" value="manager_only" :disabled="learning" />
              <span>Only Save to Broadlink Manager</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="saveDestination" value="integration_only" :disabled="learning" />
              <span>Only Save to Broadlink Integration</span>
            </label>
            <label class="radio-label">
              <input type="radio" v-model="saveDestination" value="both" :disabled="learning" />
              <span>Save to Both</span>
            </label>
          </div>
          <div v-if="showSaveDestinationHelp" class="help-box">
            <h4>Save Destination Options</h4>
            <ul>
              <li><strong>Only Save to Broadlink Manager (Recommended):</strong> Commands are saved only in this app's database (devices.json). This gives you full control and makes commands portable. The Broadlink Integration won't see these commands.</li>
              <li><strong>Only Save to Broadlink Integration:</strong> Commands are saved only in Home Assistant's Broadlink Integration storage. This app won't track these commands, but they'll be available to the Broadlink Integration's remote.send_command service.</li>
              <li><strong>Save to Both:</strong> Commands are saved in both places. Use this if you want commands available in both this app and the Broadlink Integration.</li>
            </ul>
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
          
          <!-- Preparing Phase -->
          <div v-if="learningPhase === 'preparing'">
            <p><strong>Preparing device...</strong></p>
            <small>Connecting and authenticating with Broadlink device (this takes a few seconds)</small>
          </div>
          
          <!-- IR Learning Instructions -->
          <div v-else-if="commandType === 'ir'">
            <p><strong>Ready!</strong> Point your remote at the Broadlink device and press the button...</p>
            <small>This may take up to 30 seconds</small>
          </div>
          
          <!-- RF Learning Instructions -->
          <div v-else-if="commandType === 'rf'" class="rf-instructions">
            <p v-if="!learningStatusMessage"><strong>RF Learning - Single Action:</strong></p>
            <div v-if="!learningStatusMessage" class="rf-action">
              <strong>Press and HOLD the button for 2-3 seconds, then RELEASE</strong>
            </div>
            <!-- Real-time status from backend -->
            <div v-if="learningStatusMessage" class="rf-status">
              <strong>{{ learningStatusMessage }}</strong>
            </div>
            <div v-if="learningPhase === 'captured'" class="rf-success">
              <i class="mdi mdi-check-circle"></i>
              <span>Signal captured! Saving...</span>
            </div>
          </div>
        </div>

        <!-- Result Message (success only for learning/deleting, errors use native validation) -->
        <!-- Test command success is shown inline on the command row -->
        <div v-if="resultMessage && resultType === 'success' && !resultMessage.includes('sent successfully')" class="result-message success">
          <i class="mdi mdi-check-circle"></i>
          <p>{{ resultMessage }}</p>
        </div>
        </form>

        <!-- Section Divider -->
        <div v-if="learnedCommands.length > 0 || untrackedCommands.length > 0" class="section-divider"></div>

        <!-- Loading Commands -->
        <div v-if="loadingCommands" class="loading-commands">
          <div class="loading-spinner">
            <i class="mdi mdi-loading mdi-spin"></i>
            <p>Loading commands...</p>
          </div>
        </div>

        <!-- Learned Commands List -->
        <div v-else-if="learnedCommands.length > 0" class="learned-commands">
          <h3>Tracked Commands ({{ learnedCommands.length }})</h3>
          <div class="command-list">
            <div v-for="cmd in learnedCommands" :key="cmd.name" class="command-item">
              <div class="command-info">
                <span class="command-name">{{ cmd.label || cmd.name }}</span>
              </div>
              
              <!-- Right-aligned icons and buttons -->
              <div class="command-right">
                <!-- Learned status - just checkmark with tooltip -->
                <i 
                  class="mdi mdi-check-circle learned-icon" 
                  :title="`Learned (${(cmd.type || 'ir').toUpperCase()})`"
                ></i>
                
                <!-- Command type badge -->
                <span class="command-type-badge" :class="cmd.type || 'ir'">
                  {{ (cmd.type || 'ir').toUpperCase() }}
                </span>
                
                <!-- Action buttons -->
                <div class="command-actions">
                  <button type="button" @click="testCommand(cmd.name)" class="icon-btn" title="Test command" :disabled="testingCommand === cmd.name">
                    <i class="mdi mdi-play" :class="{ 'mdi-spin': testingCommand === cmd.name }"></i>
                  </button>
                  <button type="button" @click="deleteCommand(cmd.name)" class="icon-btn danger" title="Delete and re-learn">
                    <i class="mdi mdi-delete"></i>
                  </button>
                </div>
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
      </div>

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
      :message="`Delete command '${commandToDelete}' from Broadlink Manager?`"
      checkboxLabel="Also delete from Broadlink Integration storage"
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
const saveDestination = ref('manager_only') // manager_only, integration_only, both
const showSaveDestinationHelp = ref(false)
const learning = ref(false)
const learningPhase = ref('') // 'preparing', 'ready', 'learning', 'captured', or ''
const learningStatusMessage = ref('') // Real-time status message from backend
const resultMessage = ref('')
const resultType = ref('success')
const learnedCommands = ref([])
const untrackedCommands = ref([])
const loadingCommands = ref(false)
const showDeleteConfirm = ref(false)
const commandToDelete = ref('')
const showImportConfirm = ref(false)
const commandSelect = ref(null)
const customCommandInput = ref(null)
const testedCommand = ref('') // Track which command was just tested
const testingCommand = ref('') // Track which command is currently being tested

const isSmartIR = computed(() => {
  return props.device.device_type === 'smartir'
})

const canLearn = computed(() => {
  // SmartIR devices can't learn commands
  if (isSmartIR.value) return false
  
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

// Watch for device prop changes and reload commands
watch(() => props.device, async (newDevice, oldDevice) => {
  if (newDevice && oldDevice && newDevice.id === oldDevice.id) {
    // Same device but commands may have changed
    const newCommandCount = Object.keys(newDevice.commands || {}).length
    const oldCommandCount = Object.keys(oldDevice.commands || {}).length
    
    if (newCommandCount !== oldCommandCount) {
      console.log(`🔄 Device commands changed (${oldCommandCount} -> ${newCommandCount}), reloading...`)
      await loadLearnedCommands(true) // Force reload
    }
  }
}, { deep: true })

onMounted(async () => {
  await loadBroadlinkDevices()
  
  // Sync command types on mount (fixes RF/IR detection for adopted devices)
  // Do this BEFORE loading commands so we get the updated types
  try {
    console.log('🔄 Syncing command types...')
    const syncResponse = await api.post('/api/commands/sync')
    console.log('✅ Command types synced:', syncResponse.data)
  } catch (error) {
    console.error('⚠️ Failed to sync command types:', error)
  }
  
  // Always force reload from API for non-SmartIR devices to get fresh command types
  // This ensures we get the updated RF/IR types after sync
  const shouldForceReload = !isSmartIR.value
  console.log(`📋 Will ${shouldForceReload ? 'FORCE RELOAD' : 'use cached'} commands`)
  
  // Load commands AFTER sync completes
  await loadLearnedCommands(shouldForceReload)
  // Note: Untracked commands are now synced via the sync button, not auto-imported
  
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

const loadLearnedCommands = async (forceReload = false) => {
  loadingCommands.value = true
  try {
    if (isSmartIR.value) {
      // For SmartIR devices, load commands from the code file
      const response = await api.get('/api/smartir/codes/code', {
        params: {
          entity_type: props.device.entity_type,
          code_id: props.device.device_code
        }
      })
      
      if (response.data.success && response.data.code) {
        const commands = response.data.code.commands || {}
        const commandType = response.data.code.commandType || 'ir'  // Get type from profile
        
        // For climate devices, flatten temperature-based commands
        if (props.device.entity_type === 'climate') {
          const flatCommands = []
          
          for (const [mode, value] of Object.entries(commands)) {
            if (typeof value === 'string') {
              // Simple command (e.g., "off")
              flatCommands.push({ name: mode, type: commandType })
            } else if (typeof value === 'object' && value !== null) {
              // Temperature-based command (e.g., "cool": {"16": "code1", "17": "code2"})
              // Show all available temperatures
              const temps = Object.keys(value).sort((a, b) => parseInt(a) - parseInt(b))
              
              temps.forEach(temp => {
                flatCommands.push({ 
                  name: `${mode}_${temp}`, 
                  type: commandType,
                  label: `${mode.charAt(0).toUpperCase() + mode.slice(1)} ${temp}°C`
                })
              })
            }
          }
          
          learnedCommands.value = flatCommands
        } else {
          // For non-climate devices, use command names directly
          learnedCommands.value = Object.keys(commands).map(name => ({
            name,
            type: commandType
          }))
        }
      }
    } else {
      // For Broadlink devices, always fetch from API if forceReload is true (after sync)
      console.log('📋 Loading commands for device:', props.device)
      console.log('📋 Device ID:', props.device.id)
      console.log('📋 Force reload:', forceReload)
      
      if (forceReload && props.device.id) {
        // Force reload from API to get updated command types
        console.log('🔄 Force reloading commands from API after sync')
        try {
          const response = await api.get(`/api/commands/${props.device.id}`)
          const commands = response.data.commands || {}
          console.log('📦 Raw commands from API:', commands)
          
          learnedCommands.value = Object.entries(commands).map(([name, data]) => {
            console.log(`  Command '${name}':`, data, `(type: ${typeof data})`)
            // Handle both string and object formats
            const cmdType = typeof data === 'object' && data !== null 
              ? (data.command_type || data.type || 'ir')
              : 'ir'
            return {
              name,
              type: cmdType
            }
          })
          console.log('📋 Reloaded commands:', learnedCommands.value)
        } catch (cmdError) {
          console.error('❌ Error loading commands:', cmdError)
          if (cmdError.response?.status === 404) {
            console.log('ℹ️ No commands found for device')
            learnedCommands.value = []
          } else {
            throw cmdError
          }
        }
      } else if (props.device.commands && Object.keys(props.device.commands).length > 0) {
        console.log('✅ Using commands from device object')
        learnedCommands.value = Object.entries(props.device.commands).map(([name, data]) => ({
          name,
          type: data.command_type || data.type || 'ir'
        }))
      } else if (props.device.commands !== undefined) {
        // Device has commands property but it's empty - no need to fetch
        console.log('ℹ️ Device has empty commands object - skipping API call')
        learnedCommands.value = []
      } else if (props.device.id) {
        // Commands property doesn't exist - try fetching from API
        console.log('🌐 Fetching commands from API for device ID:', props.device.id)
        try {
          const response = await api.get(`/api/commands/${props.device.id}`)
          const commands = response.data.commands || {}
          learnedCommands.value = Object.entries(commands).map(([name, data]) => ({
            name,
            type: data.command_type || data.type || 'ir'
          }))
        } catch (cmdError) {
          // 404 is expected for new devices with no commands yet
          if (cmdError.response?.status === 404) {
            console.log('ℹ️ No commands found for device (this is normal for new devices)')
            learnedCommands.value = []
          } else {
            throw cmdError // Re-throw unexpected errors
          }
        }
      } else {
        console.log('⚠️ No commands found and no device ID')
      }
      
      console.log('📋 Final learned commands:', learnedCommands.value)
    }
  } catch (error) {
    console.error('Error loading commands:', error)
  } finally {
    loadingCommands.value = false
  }
}

const startLearning = async () => {
  // Clear previous success messages
  resultMessage.value = ''
  resultType.value = ''
  learningStatusMessage.value = ''
  
  learning.value = true
  learningPhase.value = 'preparing'
  
  try {
    // Get the actual command name (either selected or custom)
    const actualCommand = commandName.value === '__custom__' ? customCommandName.value : commandName.value
    
    // Use HA API method (works in both standalone and add-on modes)
    // Note: Direct learning endpoint (/commands/learn/direct/stream) is kept in backend
    // but not used to avoid network isolation issues in add-on mode
    learningPhase.value = 'learning'
    
    const response = await api.post('/api/commands/learn', {
      device_id: props.device.id,
      entity_id: selectedBroadlink.value || props.device.broadlink_entity,
      device: props.device.device || props.device.id,
      command: actualCommand.trim(),
      command_type: commandType.value,
      save_destination: saveDestination.value
    })
    
    // Handle simple response (no SSE streaming)
    if (response.data.success) {
      learningPhase.value = 'complete'
      resultMessage.value = response.data.message || `Command "${actualCommand}" learned successfully!`
      resultType.value = 'success'
      
      // Immediately add to learned commands list
      const existingCommand = learnedCommands.value.find(cmd => cmd.name === actualCommand)
      if (!existingCommand) {
        learnedCommands.value.push({
          name: actualCommand,
          type: commandType.value
        })
      }
      
      // Remove from untracked if it was there
      const untrackedIndex = untrackedCommands.value.indexOf(actualCommand)
      if (untrackedIndex > -1) {
        untrackedCommands.value.splice(untrackedIndex, 1)
      }
      
      // Reload untracked commands
      loadUntrackedCommands()
      
      // Clear form for next command
      commandName.value = ''
      customCommandName.value = ''
      
      // Notify parent
      emit('learned', { 
        deviceId: props.device.id,
        commandName: actualCommand,
        commandType: commandType.value
      })
      
      learning.value = false
      learningPhase.value = ''
    } else {
      throw new Error(response.data.error || 'Failed to learn command')
    }
  } catch (error) {
    console.error('Learning error:', error)
    resultMessage.value = error.message || 'Error learning command'
    resultType.value = 'error'
    learning.value = false
    learningPhase.value = ''
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
    
    // For SmartIR devices, use controller_device; for Broadlink devices, use broadlink_entity
    const entityId = isSmartIR.value 
      ? props.device.controller_device 
      : (selectedBroadlink.value || props.device.broadlink_entity)
    
    // Validate required fields
    if (!entityId) {
      console.error('Missing entity_id for test command:', {
        isSmartIR: isSmartIR.value,
        controller_device: props.device.controller_device,
        broadlink_entity: props.device.broadlink_entity,
        selectedBroadlink: selectedBroadlink.value,
        device: props.device
      })
      resultMessage.value = 'Missing Broadlink remote entity. Please select a Broadlink device.'
      resultType.value = 'error'
      testingCommand.value = ''
      return
    }
    
    const requestData = {
      device_id: props.device.id,
      entity_id: entityId,
      command: command,
      device: props.device.device || props.device.id
    }
    
    console.log('🧪 Testing command:', requestData)
    
    // Use HA API test endpoint (works in add-on mode)
    const response = await api.post('/api/commands/test', requestData)
    
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
    console.error('❌ Test command error:', error)
    const errorMsg = error.response?.data?.error || error.message || 'Unknown error'
    resultMessage.value = `Failed to send command: ${errorMsg}`
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

const handleDeleteConfirm = async (alsoDeleteFromIntegration) => {
  const command = commandToDelete.value
  showDeleteConfirm.value = false
  
  try {
    console.log(`🗑️ Deleting command: ${command}, alsoDeleteFromIntegration: ${alsoDeleteFromIntegration}`)
    
    // Delete from Broadlink Manager (devices.json)
    await api.delete(`/api/commands/${props.device.id}/${command}`)
    
    // If checkbox was checked, also delete from Broadlink Integration storage
    if (alsoDeleteFromIntegration) {
      try {
        const deviceName = props.device.device || props.device.id
        await api.post('/api/commands/delete-from-storage', {
          device: deviceName,
          command: command
        })
        console.log(`✅ Also deleted from Broadlink Integration storage`)
      } catch (storageError) {
        console.warn(`⚠️ Failed to delete from Broadlink Integration storage:`, storageError)
        // Don't fail the whole operation if storage deletion fails
      }
    }
    
    // Reload commands from server to get actual state
    await loadLearnedCommands(true)
    
    // Refresh untracked commands (in case it becomes untracked)
    await loadUntrackedCommands()
    
    resultMessage.value = `Command "${command}" deleted`
    resultType.value = 'success'
    
    // Emit event to parent to refresh device list and update command count
    emit('learned', {
      deviceId: props.device.id,
      commandName: command,
      action: 'deleted'
    })
  } catch (error) {
    console.error('❌ Delete error:', error)
    resultMessage.value = `Failed to delete command: ${error.message}`
    resultType.value = 'error'
    // On error, reload to get accurate state
    await loadLearnedCommands(true)
  } finally {
    commandToDelete.value = ''
  }
}

const loadUntrackedCommands = async () => {
  try {
    // Get device name from device object
    let deviceName = props.device.device
    if (!deviceName) {
      // If device field is not set, try to extract from ID
      deviceName = props.device.id.includes('.') 
        ? props.device.id.split('.')[1] 
        : props.device.id
    }
    
    console.log('🔍 Looking for untracked commands for device:', deviceName)
    
    // Get all untracked commands
    const response = await api.get('/api/commands/untracked')
    const untracked = response.data.untracked || {}
    
    console.log('📦 All untracked commands:', Object.keys(untracked))
    console.log('📦 Untracked for this device:', untracked[deviceName])
    
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
      
      // CRITICAL: Force reload from server to get actual state
      await loadLearnedCommands(true)  // ← Added forceReload=true
      await loadUntrackedCommands()
      
      // Emit event to parent to refresh device list and update command count
      emit('learned', {
        deviceId: props.device.id,
        action: 'imported',
        count: response.data.imported_count
      })
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
  min-height: 0;
}

.smartir-info {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(33, 150, 243, 0.1);
  border-left: 3px solid rgba(33, 150, 243, 0.6);
  border-radius: 6px;
  margin-bottom: 20px;
}

.smartir-info i {
  font-size: 24px;
  color: rgba(33, 150, 243, 0.9);
  flex-shrink: 0;
}

.smartir-info h3 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
}

.smartir-info p {
  margin: 0;
  font-size: 14px;
  color: var(--ha-text-secondary-color);
  line-height: 1.5;
}

.smartir-info strong {
  color: var(--ha-text-primary-color);
  font-weight: 600;
}

.climate-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 10px;
  background: rgba(255, 152, 0, 0.1);
  border-left: 3px solid #ff9800;
  border-radius: 4px;
}

.climate-note i {
  font-size: 18px !important;
  color: #ff9800 !important;
  margin-top: 2px;
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
  font-size: 12px;
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

.loading-commands {
  margin-top: 24px;
  padding: 32px;
  text-align: center;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--ha-text-secondary-color);
}

.loading-spinner i {
  font-size: 32px;
  color: var(--ha-primary-color);
}

.loading-spinner p {
  margin: 0;
  font-size: 14px;
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
  gap: 4px;
}

.command-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px;
  background: var(--ha-card-background);
  border-radius: 8px;
  border: 2px solid #4caf50;
}

.command-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.command-name {
  font-family: monospace;
  color: var(--ha-text-primary-color);
  font-weight: 500;
  padding-left: 8px;
  font-size: 16px;
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

.command-right {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.learned-icon {
  font-size: 18px;
  color: #4caf50;
  cursor: help;
}

.command-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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
  display: flex;
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

.icon-btn i {
  font-size: 18px;
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

.rf-instructions {
  text-align: left;
  background: rgba(3, 169, 244, 0.1);
  padding: 12px;
  border-radius: 4px;
  border-left: 3px solid var(--ha-primary-color);
  font-size: 14px;
}

.rf-instructions p {
  margin: 6px 0;
}

.rf-instructions p:first-child {
  margin-top: 0;
}

.rf-instructions ol {
  margin: 8px 0;
  padding-left: 20px;
}

.rf-instructions li {
  margin: 4px 0;
  line-height: 1.4;
}

.rf-instructions .ha-note {
  margin-top: 8px;
  margin-bottom: 0;
  padding: 8px;
  background: rgba(255, 193, 7, 0.15);
  border-radius: 4px;
  font-size: 13px;
  color: var(--ha-text-primary-color);
  border-left: 3px solid #ffc107;
}

.rf-instructions .ha-note i {
  color: #ffc107;
}

.rf-instructions .rf-action {
  margin: 12px 0;
  padding: 12px;
  background: rgba(76, 175, 80, 0.1);
  border-left: 4px solid #4caf50;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.rf-instructions .rf-note {
  margin-top: 12px;
  padding: 10px;
  background: rgba(33, 150, 243, 0.1);
  border-left: 3px solid #2196f3;
  border-radius: 4px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.rf-instructions .rf-note i {
  color: #2196f3;
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 24px;
  border-top: 1px solid var(--ha-border-color);
  background: var(--ha-card-background);
  flex-shrink: 0;
}

@media (max-width: 767px) {
  .modal-overlay {
    padding: 0;
  }
  
  .modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
    margin: 0;
  }

  .modal-header {
    padding: 12px 16px;
  }

  .modal-header h2 {
    font-size: 16px;
  }

  .modal-body {
    padding: 16px;
  }

  .modal-footer {
    padding: 12px 16px;
    flex-direction: column-reverse;
  }

  .modal-footer button {
    width: 100%;
  }

  /* Command list items */
  .command-item {
    padding: 12px;
    flex-wrap: wrap;
  }

  .command-info {
    flex: 1 1 100%;
    margin-bottom: 8px;
  }

  .command-right {
    flex: 1 1 100%;
    margin-left: 0;
    justify-content: flex-end;
  }

  .command-actions {
    gap: 6px;
  }

  .command-actions button {
    min-width: 40px;
  }

  .learned-icon {
    font-size: 20px;
  }

  /* Tracked commands section */
  .tracked-commands-header h3 {
    font-size: 16px;
  }

  /* Form groups */
  .form-group label {
    font-size: 14px;
  }

  .form-group input,
  .form-group select {
    font-size: 14px;
  }

  /* SmartIR info */
  .smartir-info {
    padding: 12px;
  }

  .smartir-info h3 {
    font-size: 16px;
  }

  .smartir-info p {
    font-size: 13px;
  }
}

/* Help button and box */
.help-btn {
  background: none;
  border: none;
  color: var(--ha-primary-color, #03a9f4);
  cursor: pointer;
  padding: 0;
  margin-left: 8px;
  font-size: 18px;
  vertical-align: middle;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.help-btn:hover {
  opacity: 1;
}

.help-box {
  margin-top: 12px;
  padding: 16px;
  background: var(--ha-card-background, #1c1c1c);
  border: 1px solid var(--ha-divider-color, #2c2c2c);
  border-radius: 8px;
  font-size: 14px;
}

.help-box h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: var(--ha-primary-color, #03a9f4);
}

.help-box ul {
  margin: 0;
  padding-left: 20px;
}

.help-box li {
  margin-bottom: 12px;
  line-height: 1.5;
}

.help-box li:last-child {
  margin-bottom: 0;
}

.help-box strong {
  color: var(--ha-primary-text-color, #e1e1e1);
}
</style>
