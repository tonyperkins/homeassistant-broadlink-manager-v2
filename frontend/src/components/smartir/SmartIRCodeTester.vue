<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <!-- Header -->
      <div class="modal-header">
        <h3>
          <i class="mdi mdi-test-tube"></i>
          Test SmartIR Code
        </h3>
        <button @click="close" class="close-btn">
          <i class="mdi mdi-close"></i>
        </button>
      </div>

      <!-- Body -->
      <div class="modal-body">
        <!-- Step 1: Code Selection -->
        <div v-if="!selectedCode" class="selection-section">
          <div class="info-banner">
            <i class="mdi mdi-information"></i>
            <p>Select a SmartIR code from the index to test commands with your Broadlink device.</p>
          </div>

          <div class="form-group">
            <label>
              <i class="mdi mdi-shape"></i>
              Platform
            </label>
            <select v-model="platform" @change="onPlatformChange" class="form-select">
              <option value="climate">Climate (AC/Heater)</option>
              <option value="media_player">Media Player (TV/Audio)</option>
              <option value="fan">Fan</option>
              <option value="light">Light</option>
            </select>
          </div>

          <div class="form-group">
            <SearchableDropdown
              v-model="manufacturer"
              :options="manufacturers"
              label="Manufacturer"
              placeholder="Search manufacturers..."
              :loading="loadingManufacturers"
              :disabled="loadingManufacturers"
              @change="onManufacturerChange"
            />
          </div>

          <div class="form-group">
            <SearchableDropdown
              v-model="selectedModelCode"
              :options="modelOptions"
              :option-label="'label'"
              :option-value="'code'"
              label="Model"
              placeholder="Search models..."
              :loading="loadingModels"
              :disabled="!manufacturer || loadingModels"
              @change="onModelChange"
            />
          </div>

          <div v-if="selectedModel" class="code-info">
            <i class="mdi mdi-information-outline"></i>
            <div>
              <strong>{{ manufacturer }} - {{ selectedModel.models[0] }}</strong>
              <p>Code: {{ selectedModel.code }}</p>
            </div>
          </div>

          <div class="form-actions">
            <button 
              @click="loadCode" 
              :disabled="!selectedModel || loading"
              class="btn-primary"
            >
              <i class="mdi" :class="loading ? 'mdi-loading mdi-spin' : 'mdi-download'"></i>
              {{ loading ? 'Loading...' : 'Load Commands' }}
            </button>
          </div>
        </div>

        <!-- Step 2: Command Testing -->
        <div v-else class="testing-section">
          <!-- Code Info -->
          <div class="code-header">
            <div class="code-details">
              <h4>{{ codeData.manufacturer }} - {{ codeData.supportedModels?.[0] || 'Unknown' }}</h4>
              <span class="code-badge">Code: {{ selectedCode }}</span>
            </div>
            <button @click="resetSelection" class="btn-secondary-small">
              <i class="mdi mdi-arrow-left"></i>
              Change Code
            </button>
          </div>

          <!-- Broadlink Device Selector -->
          <div class="device-selector">
            <label>
              <i class="mdi mdi-remote"></i>
              Broadlink Device
            </label>
            <select v-model="selectedDevice" class="form-select">
              <option value="">Select device to test with...</option>
              <option v-for="device in broadlinkDevices" :key="device.entity_id" :value="device.entity_id">
                {{ device.friendly_name || device.entity_id }}
              </option>
            </select>
          </div>

          <!-- Commands List -->
          <div class="commands-section">
            <div class="commands-header">
              <h5>Sample Commands ({{ filteredCommands.length }} / {{ commandsList.length }})</h5>
              <span v-if="testedCommands.size > 0" class="tested-count">
                {{ testedCommands.size }} tested
              </span>
            </div>

            <!-- Filters (only show for climate) -->
            <div v-if="platform === 'climate' && commandsList.length > 0" class="filters-section">
              <div class="filter-row">
                <input 
                  v-model="searchQuery" 
                  type="text" 
                  placeholder="Search commands..."
                  class="search-input"
                >
              </div>
              <div class="filter-row">
                <select v-model="filterMode" class="filter-select">
                  <option value="">All Modes</option>
                  <option value="cool">Cool</option>
                  <option value="heat">Heat</option>
                  <option value="off">Off</option>
                </select>
                <select v-model="filterFanSpeed" class="filter-select">
                  <option value="">All Fan Speeds</option>
                  <option value="low">Low</option>
                  <option value="mid">Mid</option>
                  <option value="high">High</option>
                  <option value="auto">Auto</option>
                </select>
                <select v-model="filterSwing" class="filter-select">
                  <option value="">All Swing</option>
                  <option value="stop">Stop</option>
                  <option value="swing">Swing</option>
                </select>
                <button @click="clearFilters" class="btn-clear-filters" v-if="hasActiveFilters">
                  <i class="mdi mdi-filter-remove"></i>
                  Clear
                </button>
              </div>
            </div>

            <div v-if="commandsList.length === 0" class="empty-state">
              <i class="mdi mdi-alert-circle"></i>
              <p>No commands found in this code</p>
            </div>

            <div v-else-if="filteredCommands.length === 0" class="empty-state">
              <i class="mdi mdi-filter-off"></i>
              <p>No commands match your filters</p>
              <button @click="clearFilters" class="btn-secondary-small">
                Clear Filters
              </button>
            </div>

            <div v-else class="commands-list">
              <div 
                v-for="cmd in filteredCommands" 
                :key="cmd.name"
                class="command-item"
                :class="{ 
                  'tested': testedCommands.has(cmd.name),
                  'testing': testingCommand === cmd.name 
                }"
              >
                <div class="command-name">
                  <i class="mdi" :class="getCommandIcon(cmd.mode || cmd.name)"></i>
                  <span>{{ cmd.label || cmd.name }}</span>
                </div>
                <div class="command-actions">
                  <span v-if="testedCommands.has(cmd.name)" class="status-badge success">
                    <i class="mdi mdi-check"></i>
                    Tested
                  </span>
                  <button 
                    @click="testCommand(cmd.name)"
                    :disabled="!selectedDevice || testingCommand === cmd.name"
                    class="btn-test"
                  >
                    <i class="mdi" :class="testingCommand === cmd.name ? 'mdi-loading mdi-spin' : 'mdi-play'"></i>
                    Test
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="modal-actions">
            <button @click="downloadJson" class="btn-primary">
              <i class="mdi mdi-download"></i>
              Download JSON
            </button>
            <button @click="close" class="btn-secondary">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import SearchableDropdown from '../common/SearchableDropdown.vue'
import api from '@/services/api'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'clone'])

const toast = inject('toast')

// State
const platform = ref('climate')
const manufacturer = ref('')
const manufacturers = ref([])
const loadingManufacturers = ref(false)

const selectedModel = ref(null)
const selectedModelCode = ref('')
const models = ref([])
const loadingModels = ref(false)

// Model options for SearchableDropdown
const modelOptions = computed(() => {
  return models.value.map(model => ({
    code: model.code,
    label: `${model.models.join(', ')} (Code: ${model.code})`,
    value: model.code
  }))
})

const selectedCode = ref(null)
const codeData = ref(null)
const loading = ref(false)

const broadlinkDevices = ref([])
const selectedDevice = ref('')

const commandsList = ref([])
const testedCommands = ref(new Set())
const testingCommand = ref(null)

// Filter state
const searchQuery = ref('')
const filterMode = ref('')
const filterFanSpeed = ref('')
const filterSwing = ref('')

// Computed: Filtered commands
const filteredCommands = computed(() => {
  let filtered = commandsList.value

  // Text search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(cmd => 
      (cmd.label || cmd.name).toLowerCase().includes(query)
    )
  }

  // Mode filter
  if (filterMode.value) {
    filtered = filtered.filter(cmd => cmd.mode === filterMode.value)
  }

  // Fan speed filter
  if (filterFanSpeed.value) {
    filtered = filtered.filter(cmd => cmd.fanSpeed === filterFanSpeed.value)
  }

  // Swing filter
  if (filterSwing.value) {
    filtered = filtered.filter(cmd => cmd.swingMode === filterSwing.value)
  }

  return filtered
})

// Computed: Check if any filters are active
const hasActiveFilters = computed(() => {
  return searchQuery.value || filterMode.value || filterFanSpeed.value || filterSwing.value
})

// Load manufacturers when platform changes
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    loadManufacturers()
    loadBroadlinkDevices()
  }
})

watch(platform, () => {
  if (props.isOpen) {
    manufacturer.value = ''
    selectedModel.value = null
    models.value = []
    loadManufacturers()
  }
})

async function loadManufacturers() {
  loadingManufacturers.value = true
  try {
    const response = await api.get('/api/smartir/codes/manufacturers', {
      params: { entity_type: platform.value }
    })
    manufacturers.value = response.data.manufacturers || []
  } catch (err) {
    console.error('Error loading manufacturers:', err)
    toast.value?.error('Failed to load manufacturers', '❌ Error')
  } finally {
    loadingManufacturers.value = false
  }
}

async function loadModels() {
  if (!manufacturer.value) return
  
  loadingModels.value = true
  try {
    const response = await api.get('/api/smartir/codes/models', {
      params: {
        entity_type: platform.value,
        manufacturer: manufacturer.value
      }
    })
    models.value = response.data.models || []
  } catch (err) {
    console.error('Error loading models:', err)
    toast.value?.error('Failed to load models', '❌ Error')
  } finally {
    loadingModels.value = false
  }
}

async function loadBroadlinkDevices() {
  try {
    const response = await api.get('/api/remote/devices')
    broadlinkDevices.value = response.data.devices || []
  } catch (err) {
    console.error('Error loading Broadlink devices:', err)
  }
}

async function loadCode() {
  if (!selectedModel.value) return
  
  loading.value = true
  try {
    const response = await api.get('/api/smartir/codes/code', {
      params: {
        entity_type: platform.value,
        code_id: selectedModel.value.code
      }
    })
    codeData.value = response.data.code
    selectedCode.value = selectedModel.value.code
    
    // Extract commands
    extractCommands(response.data.code)
    
    toast.value?.success(`Loaded ${commandsList.value.length} commands`, '✅ Code Loaded')
  } catch (err) {
    console.error('Error loading code:', err)
    toast.value?.error(err.message || 'Failed to load code', '❌ Error')
  } finally {
    loading.value = false
  }
}

function extractCommands(code) {
  const commands = []
  
  if (!code.commands) {
    commandsList.value = commands
    return
  }
  
  // Check if this is a climate device (nested structure)
  const isClimate = platform.value === 'climate'
  
  if (isClimate) {
    // Climate structure: mode → fanSpeed → swing → temperature → base64
    // Example: cool → auto → stop → 16 → "JgBQAAA..."
    const modes = code.commands
    
    for (const [mode, fanSpeeds] of Object.entries(modes)) {
      if (mode === 'off') {
        // Off command is a direct string
        if (typeof fanSpeeds === 'string') {
          commands.push({
            name: 'off',
            label: 'OFF',
            data: fanSpeeds,
            mode: 'off'
          })
        }
        continue
      }
      
      if (typeof fanSpeeds !== 'object') continue
      
      for (const [fanSpeed, swingModes] of Object.entries(fanSpeeds)) {
        if (typeof swingModes !== 'object') continue
        
        for (const [swingMode, temperatures] of Object.entries(swingModes)) {
          if (typeof temperatures !== 'object') continue
          
          // Get a representative temperature (first one, or 24 if available)
          const tempKeys = Object.keys(temperatures)
          const defaultTemp = tempKeys.includes('24') ? '24' : tempKeys[0]
          
          if (defaultTemp && typeof temperatures[defaultTemp] === 'string') {
            const commandName = `${mode}_${defaultTemp}_${fanSpeed}_${swingMode}`
            const label = `${mode.toUpperCase()} ${defaultTemp}°C ${fanSpeed} ${swingMode}`
            
            commands.push({
              name: commandName,
              label: label,
              data: temperatures[defaultTemp],
              mode: mode,
              temperature: defaultTemp,
              fanSpeed: fanSpeed,
              swingMode: swingMode
            })
          }
        }
      }
    }
  } else {
    // Simple flat structure for media_player, fan, light
    // Commands are direct key-value pairs
    for (const [key, value] of Object.entries(code.commands)) {
      if (typeof value === 'string') {
        commands.push({
          name: key,
          label: key.toUpperCase().replace(/_/g, ' '),
          data: value
        })
      }
    }
  }
  
  commandsList.value = commands
}

async function testCommand(commandName) {
  if (!selectedDevice.value) {
    toast.value?.warning('Please select a Broadlink device first', '⚠️ No Device')
    return
  }
  
  testingCommand.value = commandName
  
  try {
    // Find the command in our extracted list
    const command = commandsList.value.find(cmd => cmd.name === commandName)
    
    if (!command || !command.data) {
      throw new Error(`Command "${commandName}" not found`)
    }
    
    // Send raw command using the send-raw endpoint
    await api.post('/api/commands/send-raw', {
      entity_id: selectedDevice.value,
      command: command.data,
      command_type: 'ir'
    })
    
    testedCommands.value.add(commandName)
    toast.value?.success(`Command sent: ${command.label || commandName}`, '✅ Tested')
  } catch (err) {
    console.error('Error testing command:', err)
    toast.value?.error(`Failed to test command`, '❌ Error')
  } finally {
    testingCommand.value = null
  }
}

function downloadJson() {
  if (!codeData.value) {
    toast.value?.error('No profile data to download', '❌ Error')
    return
  }
  
  try {
    // Create filename from manufacturer and model
    const manufacturer = codeData.value.manufacturer || 'unknown'
    const model = codeData.value.supportedModels?.[0] || selectedCode.value
    const filename = `${manufacturer.toLowerCase().replace(/\s+/g, '_')}_${model.toLowerCase().replace(/\s+/g, '_')}.json`
    
    // Create blob and download
    const jsonString = JSON.stringify(codeData.value, null, 2)
    const blob = new Blob([jsonString], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    toast.value?.success(
      `Downloaded ${filename}`,
      '✅ Download Complete'
    )
  } catch (err) {
    console.error('Error downloading JSON:', err)
    toast.value?.error(err.message || 'Failed to download JSON', '❌ Download Error')
  }
}

function onPlatformChange() {
  manufacturer.value = ''
  selectedModel.value = null
  selectedModelCode.value = ''
  models.value = []
}

function onManufacturerChange() {
  selectedModel.value = null
  selectedModelCode.value = ''
  loadModels()
}

function onModelChange() {
  // Find the selected model object from the code
  if (selectedModelCode.value) {
    selectedModel.value = models.value.find(m => m.code === selectedModelCode.value)
  } else {
    selectedModel.value = null
  }
}

function clearFilters() {
  searchQuery.value = ''
  filterMode.value = ''
  filterFanSpeed.value = ''
  filterSwing.value = ''
}

function resetSelection() {
  selectedCode.value = null
  codeData.value = null
  commandsList.value = []
  testedCommands.value.clear()
  testingCommand.value = null
  clearFilters()
}

function getCommandIcon(commandName) {
  const name = commandName.toLowerCase()
  if (name.includes('power') || name.includes('off') || name === 'off') return 'mdi-power'
  if (name.includes('cool')) return 'mdi-snowflake'
  if (name.includes('heat')) return 'mdi-fire'
  if (name.includes('fan')) return 'mdi-fan'
  if (name.includes('auto')) return 'mdi-auto-fix'
  if (name.includes('dry')) return 'mdi-water-percent'
  if (name.includes('temp')) return 'mdi-thermometer'
  if (name.includes('swing')) return 'mdi-swap-vertical'
  return 'mdi-remote'
}

function close() {
  resetSelection()
  manufacturer.value = ''
  selectedModel.value = null
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-container {
  background: var(--ha-card-background);
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--ha-divider-color);
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
}

.modal-header h3 i {
  font-size: 24px;
  color: var(--ha-primary-color);
}

.close-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--ha-text-secondary-color);
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--ha-divider-color);
  color: var(--ha-text-primary-color);
}

.close-btn i {
  font-size: 24px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Selection Section */
.selection-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-banner {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(3, 169, 244, 0.1);
  border-left: 4px solid var(--ha-primary-color);
  border-radius: 6px;
}

.info-banner i {
  font-size: 24px;
  color: var(--ha-primary-color);
  flex-shrink: 0;
}

.info-banner p {
  margin: 0;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  line-height: 1.5;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.form-group label i {
  font-size: 18px;
  color: var(--ha-primary-color);
}

.form-select {
  padding: 12px 16px;
  background: var(--ha-card-background);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.form-select option {
  background: var(--ha-card-background);
  color: var(--ha-text-primary-color);
  padding: 8px;
}

.form-select:hover:not(:disabled) {
  border-color: var(--ha-primary-color);
  box-shadow: 0 2px 8px rgba(3, 169, 244, 0.3);
}

.form-select:focus {
  outline: none;
  border-color: var(--ha-primary-color);
  box-shadow: 0 0 0 3px rgba(3, 169, 244, 0.2), 0 2px 8px rgba(3, 169, 244, 0.3);
}

.form-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.code-info {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--ha-card-background);
  border-radius: 8px;
  border: 2px solid rgba(3, 169, 244, 0.3);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.code-info i {
  font-size: 24px;
  color: var(--ha-primary-color);
  flex-shrink: 0;
}

.code-info strong {
  display: block;
  color: var(--ha-text-primary-color);
  margin-bottom: 4px;
}

.code-info p {
  margin: 0;
  font-size: 13px;
  color: var(--ha-text-secondary-color);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
}

/* Testing Section */
.testing-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--ha-divider-color);
}

.code-details h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
}

.code-badge {
  display: inline-block;
  padding: 4px 10px;
  background: var(--ha-primary-background-color);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ha-text-secondary-color);
  font-family: monospace;
}

.device-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-selector label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
}

.device-selector label i {
  font-size: 18px;
  color: var(--ha-primary-color);
}

.commands-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.commands-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.commands-header h5 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
}

.tested-count {
  padding: 4px 10px;
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

/* Filter Controls */
.filters-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--ha-primary-background-color);
  border: 1px solid var(--ha-divider-color);
  border-radius: 8px;
}

.filter-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 10px 12px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-divider-color);
  border-radius: 6px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--ha-primary-color);
}

.filter-select {
  flex: 1;
  padding: 10px 12px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-divider-color);
  border-radius: 6px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-select:focus {
  outline: none;
  border-color: var(--ha-primary-color);
}

.btn-clear-filters {
  padding: 10px 16px;
  background: transparent;
  border: 1px solid var(--ha-divider-color);
  border-radius: 6px;
  color: var(--ha-text-secondary-color);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-clear-filters:hover {
  background: var(--ha-divider-color);
  color: var(--ha-text-primary-color);
}

.btn-clear-filters i {
  font-size: 18px;
}

.commands-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px;
}

.command-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--ha-primary-background-color);
  border: 1px solid var(--ha-divider-color);
  border-radius: 8px;
  transition: all 0.2s;
}

.command-item.tested {
  border-color: #4caf50;
  background: rgba(76, 175, 80, 0.05);
}

.command-item.testing {
  border-color: var(--ha-primary-color);
}

.command-name {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.command-name i {
  font-size: 18px;
  color: var(--ha-text-secondary-color);
}

.command-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.success {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.status-badge i {
  font-size: 14px;
}

.btn-test {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--ha-primary-color);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-test:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-test i {
  font-size: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--ha-text-secondary-color);
}

.empty-state i {
  font-size: 48px;
  opacity: 0.3;
}

.modal-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--ha-divider-color);
}

/* Buttons */
.btn-primary,
.btn-secondary,
.btn-secondary-small {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: var(--ha-primary-color);
  color: white;
  flex: 1;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  color: var(--ha-text-primary-color);
  border: 1px solid var(--ha-divider-color);
}

.btn-secondary:hover {
  background: var(--ha-divider-color);
}

.btn-secondary-small {
  padding: 6px 12px;
  font-size: 13px;
  background: transparent;
  color: var(--ha-text-primary-color);
  border: 1px solid var(--ha-divider-color);
}

.btn-secondary-small:hover {
  background: var(--ha-divider-color);
}

.btn-primary i,
.btn-secondary i,
.btn-secondary-small i {
  font-size: 18px;
}

/* Scrollbar */
.commands-list::-webkit-scrollbar {
  width: 8px;
}

.commands-list::-webkit-scrollbar-track {
  background: var(--ha-primary-background-color);
  border-radius: 4px;
}

.commands-list::-webkit-scrollbar-thumb {
  background: var(--ha-divider-color);
  border-radius: 4px;
}

.commands-list::-webkit-scrollbar-thumb:hover {
  background: var(--ha-text-secondary-color);
}
</style>
