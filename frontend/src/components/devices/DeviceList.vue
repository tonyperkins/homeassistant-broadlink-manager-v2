<template>
  <div class="device-list-card">
    <div class="card-header">
      <button class="icon-button chevron-button" @click="toggleExpanded">
        <i class="mdi" :class="isExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down'"></i>
      </button>
      <div class="header-left" @click="toggleExpanded">
        <div class="header-icon">
          <i class="mdi mdi-devices"></i>
        </div>
        <h3>Managed Devices</h3>
        <div class="header-badges">
          <span class="header-info">{{ deviceStore.deviceCount }} devices</span>
        </div>
      </div>
      <div class="header-right">
        <button 
          @click.stop="syncAllAreas" 
          class="btn btn-secondary"
          v-if="isExpanded"
          :disabled="syncingAreas"
          title="Sync all areas from Home Assistant"
        >
          <i class="mdi" :class="syncingAreas ? 'mdi-loading mdi-spin' : 'mdi-refresh'"></i>
          {{ syncingAreas ? 'Syncing...' : 'Sync Areas' }}
        </button>
        <button 
          @click.stop="generateAllEntities" 
          class="btn btn-secondary"
          v-if="isExpanded"
          :disabled="generatingEntities"
          title="Generate entities for all devices"
        >
          <i class="mdi" :class="generatingEntities ? 'mdi-loading mdi-spin' : 'mdi-file-code'"></i>
          {{ generatingEntities ? 'Generating...' : 'Generate Entities' }}
        </button>
        <button 
          @click.stop="showCreateForm = true" 
          class="btn btn-primary"
          v-if="isExpanded"
        >
          <i class="mdi mdi-plus"></i>
          Add Device
        </button>
      </div>
    </div>

    <div v-show="isExpanded" class="card-body">

    <!-- Device Discovery Banner -->
    <DeviceDiscovery ref="discoveryRef" @adopt="adoptDevice" />

    <!-- Filter Bar -->
    <div v-if="deviceStore.hasDevices" class="filter-bar">
      <!-- Search Row -->
      <div class="filter-row filter-row-search">
        <div class="filter-group filter-search">
          <label>
            <i class="mdi mdi-magnify"></i>
            <input
              v-model="filters.search"
              type="text"
              placeholder="Search devices, commands..."
              class="search-input"
            />
          </label>
        </div>
      </div>

      <!-- Filters Row -->
      <div class="filter-row filter-row-dropdowns">
        <div class="filter-group">
          <label>
            <i class="mdi mdi-access-point"></i>
            <select v-model="filters.broadlinkDevice">
              <option value="">All Controller Devices</option>
              <option v-for="device in broadlinkDeviceOptions" :key="device.entity_id" :value="device.entity_id">
                {{ device.friendly_name }}
              </option>
            </select>
          </label>
        </div>

        <div class="filter-group">
          <label>
            <i class="mdi mdi-home-map-marker"></i>
            <select v-model="filters.area">
              <option value="">All Areas</option>
              <option v-for="area in areaOptions" :key="area" :value="area">
                {{ area }}
              </option>
            </select>
          </label>
        </div>

        <div class="filter-group">
          <label>
            <i class="mdi mdi-shape"></i>
            <select v-model="filters.entityType">
              <option value="">All Types</option>
              <option value="light">Light</option>
              <option value="fan">Fan</option>
              <option value="switch">Switch</option>
              <option value="media_player">Media Player</option>
              <option value="cover">Cover</option>
              <option value="climate">Climate</option>
            </select>
          </label>
        </div>

        <div v-if="smartirInstalled" class="filter-group filter-toggle">
          <label class="toggle-label">
            <span class="toggle-text">
              <img src="@/assets/images/smartir-logo.png" alt="SmartIR" class="smartir-icon" />
              SmartIR Only
            </span>
            <input 
              type="checkbox" 
              v-model="filters.showSmartIROnly"
              class="toggle-checkbox"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <button v-if="hasActiveFilters" @click="clearFilters" class="btn-clear-filters">
          <i class="mdi mdi-filter-remove"></i>
          Clear
        </button>

        <!-- View Toggle Button Group (hidden on mobile) -->
        <div v-if="!isMobile" class="view-toggle-group">
          <button 
            @click="viewMode = 'grid'" 
            class="view-toggle-btn"
            :class="{ active: viewMode === 'grid' }"
            title="Grid View"
          >
            <i class="mdi mdi-view-grid"></i>
            Grid
          </button>
          <button 
            @click="viewMode = 'list'" 
            class="view-toggle-btn"
            :class="{ active: viewMode === 'list' }"
            title="List View"
          >
            <i class="mdi mdi-view-list"></i>
            List
          </button>
        </div>

        <div class="filter-results">
          {{ filteredDevices.length }} of {{ deviceStore.deviceCount }}
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="deviceStore.loading" class="loading-state">
      <i class="mdi mdi-loading mdi-spin"></i>
      <p>Loading devices...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="deviceStore.error" class="error-state">
      <i class="mdi mdi-alert-circle"></i>
      <p>{{ deviceStore.error }}</p>
      <button @click="deviceStore.loadDevices()" class="btn btn-secondary">
        Retry
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="!deviceStore.hasDevices" class="empty-state">
      <i class="mdi mdi-devices"></i>
      <h3>No Devices Yet</h3>
      <p>Get started by adding your first managed device</p>
      <button @click="showCreateForm = true" class="btn btn-primary">
        <i class="mdi mdi-plus"></i>
        Add Your First Device
      </button>
    </div>

    <!-- Device Grid -->
    <div v-if="viewMode === 'grid'" class="device-grid">
      <DeviceCard
        v-for="device in filteredDevices"
        :key="device.id"
        :device="device"
        :broadlink-devices="broadlinkDevices"
        @edit="editDevice"
        @delete="confirmDelete"
        @learn="learnCommands"
      />
    </div>

    <!-- Device List View -->
    <DeviceListView
      v-else-if="viewMode === 'list' && filteredDevices.length > 0"
      :devices="filteredDevices"
      @send-command="handleSendCommand"
      @edit-device="editDevice"
      @delete-device="confirmDelete"
    />

    <!-- No Results -->
    <div v-if="deviceStore.hasDevices && filteredDevices.length === 0" class="no-results">
      <i class="mdi mdi-filter-off"></i>
      <h3>No devices match your filters</h3>
      <p>Try adjusting your search or filter criteria</p>
    </div>
    </div>

    <!-- Modals (outside card-body) -->
    <DeviceForm
      v-if="showCreateForm"
      :device="selectedDevice"
      @save="handleSave"
      @cancel="closeForm"
    />

    <CommandLearner
      v-if="showCommandLearner"
      :device="selectedDevice"
      @learned="handleCommandLearned"
      @cancel="closeCommandLearner"
    />

    <ConfirmDialog
      :isOpen="showDeleteConfirm"
      :title="`Delete ${deviceToDelete?.name}?`"
      :message="deleteMessage"
      confirmText="Delete"
      cancelText="Cancel"
      :dangerMode="true"
      :checkboxLabel="deleteCheckboxLabel"
      @confirm="handleDeleteConfirm"
      @cancel="cancelDelete"
    />

    <ErrorDialog
      :isOpen="showErrorDialog"
      :title="errorDialog.title"
      :message="errorDialog.message"
      :suggestion="errorDialog.suggestion"
      :details="errorDialog.details"
      :error="errorDialog.error"
      :context="errorDialog.context"
      @close="closeErrorDialog"
    />

    <!-- Entity Generation Result Dialog -->
    <ConfirmDialog
      :isOpen="showGenerationResultDialog"
      :title="generationResult.title"
      :message="generationResult.message"
      confirmText="OK"
      :showCancel="false"
      :dangerMode="!generationResult.success"
      @confirm="closeGenerationResultDialog"
      @cancel="closeGenerationResultDialog"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useDeviceStore } from '@/stores/devices'
import { useToast } from '@/composables/useToast'
import { useResponsive } from '@/composables/useResponsive'
import DeviceCard from './DeviceCard.vue'
import DeviceListView from './DeviceListView.vue'
import DeviceForm from './DeviceForm.vue'
import CommandLearner from '../commands/CommandLearner.vue'
import ConfirmDialog from '../common/ConfirmDialog.vue'
import ErrorDialog from '../common/ErrorDialog.vue'
import DeviceDiscovery from './DeviceDiscovery.vue'
import api from '@/services/api'

const deviceStore = useDeviceStore()
const toast = useToast()
const { isMobile } = useResponsive()
const showCreateForm = ref(false)
const showCommandLearner = ref(false)
const selectedDevice = ref(null)
const showDeleteConfirm = ref(false)
const deviceToDelete = ref(null)
const discoveryRef = ref(null)
const isExpanded = ref(true)
const generatingEntities = ref(false)
const syncingAreas = ref(false)

// View mode (grid or list)
// On mobile, always use grid view; on desktop, use saved preference
const getInitialViewMode = () => {
  if (window.innerWidth <= 767) return 'grid'
  return localStorage.getItem('device_view_mode') || 'grid'
}
const viewMode = ref(getInitialViewMode())

// Watch for mobile state changes and force grid view on mobile
watch(isMobile, (newIsMobile) => {
  if (newIsMobile && viewMode.value === 'list') {
    viewMode.value = 'grid'
  }
})

const toggleViewMode = () => {
  // Don't allow list view on mobile
  if (isMobile.value && viewMode.value === 'grid') {
    return
  }
  viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
  localStorage.setItem('device_view_mode', viewMode.value)
}

// Watch viewMode changes to save preference
watch(viewMode, (newMode) => {
  localStorage.setItem('device_view_mode', newMode)
})

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

// Error dialog state
const showErrorDialog = ref(false)
const errorDialog = ref({
  title: 'Error',
  message: '',
  suggestion: '',
  details: '',
  error: null,
  context: {}
})

// Entity generation result dialog state
const showGenerationResultDialog = ref(false)
const generationResult = ref({
  success: false,
  title: '',
  message: ''
})

// Filters
const filters = ref({
  search: '',
  broadlinkDevice: '',
  area: '',
  entityType: '',
  showSmartIROnly: false
})

const broadlinkDevices = ref([])

// Inject SmartIR status
const smartirStatus = inject('smartirStatus')
const smartirEnabled = inject('smartirEnabled')
const smartirInstalled = computed(() => {
  // Check if simulating not-installed
  const isSimulating = localStorage.getItem('smartir_simulate_not_installed') === 'true'
  if (isSimulating) return false
  return smartirStatus?.value?.installed || false
})

// Filter options (computed from available devices)
const broadlinkDeviceOptions = computed(() => {
  const deviceMap = new Map()
  
  deviceStore.devices.forEach(device => {
    if (device.broadlink_entity) {
      // Find the friendly name from loaded Broadlink devices
      const blDevice = broadlinkDevices.value.find(d => d.entity_id === device.broadlink_entity)
      const friendlyName = blDevice ? (blDevice.name || device.broadlink_entity) : device.broadlink_entity
      
      deviceMap.set(device.broadlink_entity, {
        entity_id: device.broadlink_entity,
        friendly_name: friendlyName
      })
    }
  })
  
  return Array.from(deviceMap.values()).sort((a, b) => 
    a.friendly_name.localeCompare(b.friendly_name)
  )
})

const areaOptions = computed(() => {
  const areas = new Set()
  deviceStore.devices.forEach(device => {
    if (device.area) {
      areas.add(device.area)
    }
  })
  return Array.from(areas).sort()
})

// Filtered devices
const filteredDevices = computed(() => {
  let devices = deviceStore.devices

  // Text search across all fields
  if (filters.value.search) {
    const searchLower = filters.value.search.toLowerCase()
    devices = devices.filter(d => {
      // Search in device name
      if (d.name?.toLowerCase().includes(searchLower)) return true
      
      // Search in entity type
      if (d.entity_type?.toLowerCase().includes(searchLower)) return true
      
      // Search in area
      if (d.area?.toLowerCase().includes(searchLower)) return true
      
      // Search in entity ID
      if (d.id?.toLowerCase().includes(searchLower)) return true
      
      // Search in commands
      const commands = Object.keys(d.commands || {})
      if (commands.some(cmd => cmd.toLowerCase().includes(searchLower))) return true
      
      // Search in Broadlink entity (friendly name)
      const blDevice = broadlinkDevices.value.find(bd => bd.entity_id === d.broadlink_entity)
      if (blDevice?.name?.toLowerCase().includes(searchLower)) return true
      
      return false
    })
  }

  if (filters.value.broadlinkDevice) {
    devices = devices.filter(d => {
      // For SmartIR devices, check controller_device; for Broadlink devices, check broadlink_entity
      return d.broadlink_entity === filters.value.broadlinkDevice || 
             d.controller_device === filters.value.broadlinkDevice
    })
  }

  if (filters.value.area) {
    devices = devices.filter(d => d.area === filters.value.area)
  }

  if (filters.value.entityType) {
    devices = devices.filter(d => d.entity_type === filters.value.entityType)
  }

  // SmartIR filter
  if (filters.value.showSmartIROnly) {
    devices = devices.filter(d => d.device_type === 'smartir')
  }

  // Hide SmartIR devices if SmartIR integration is disabled or simulating not-installed
  const isSimulating = localStorage.getItem('smartir_simulate_not_installed') === 'true'
  if (!smartirEnabled?.value || isSimulating) {
    devices = devices.filter(d => d.device_type !== 'smartir')
  }

  return devices
})

const hasActiveFilters = computed(() => {
  return filters.value.search || filters.value.broadlinkDevice || filters.value.area || filters.value.entityType || filters.value.showSmartIROnly
})

const clearFilters = () => {
  filters.value.search = ''
  filters.value.broadlinkDevice = ''
  filters.value.area = ''
  filters.value.entityType = ''
  filters.value.showSmartIROnly = false
}

const loadBroadlinkDevices = async () => {
  try {
    // Use new endpoint that returns all remote devices (Broadlink, Xiaomi, etc.)
    const response = await api.get('/api/remote/devices')
    broadlinkDevices.value = response.data.devices || []
  } catch (error) {
    console.error('Error loading remote devices:', error)
  }
}

// Watch for viewMode changes and persist to localStorage
watch(viewMode, (newMode) => {
  localStorage.setItem('device_view_mode', newMode)
})

onMounted(async () => {
  await Promise.all([
    deviceStore.loadDevices(),
    loadBroadlinkDevices()
  ])
  
  // Note: Auto-sync removed to prevent UI flickering on page load
  // Users can manually sync areas using the "Sync Areas" button if needed
})

const editDevice = (device) => {
  selectedDevice.value = device
  showCreateForm.value = true
}

const deleteMessage = computed(() => {
  if (!deviceToDelete.value) return ''
  const commandCount = Object.keys(deviceToDelete.value.commands || {}).length
  if (commandCount === 0) {
    return 'This device has no commands. The device will be removed from tracking.'
  }
  return `This device has ${commandCount} learned command${commandCount > 1 ? 's' : ''}. What would you like to do?`
})

const deleteCheckboxLabel = computed(() => {
  if (!deviceToDelete.value) return ''
  const commandCount = Object.keys(deviceToDelete.value.commands || {}).length
  if (commandCount === 0) return ''
  return `Also delete all ${commandCount} command${commandCount > 1 ? 's' : ''} from Broadlink storage`
})

const confirmDelete = (device) => {
  deviceToDelete.value = device
  showDeleteConfirm.value = true
}

const cancelDelete = () => {
  showDeleteConfirm.value = false
  deviceToDelete.value = null
}

const handleDeleteConfirm = async (deleteCommands) => {
  const device = deviceToDelete.value
  showDeleteConfirm.value = false
  
  try {
    // Delete the device (backend will handle command deletion if requested)
    await deviceStore.deleteDevice(device.id, deleteCommands)
    
    // Refresh discovery to show newly untracked device
    if (discoveryRef.value) {
      await discoveryRef.value.refresh()
    }
  } catch (error) {
    const errorMsg = error.response?.data?.error || error.message || 'Unknown error'
    showError('Failed to Delete Device', errorMsg)
  } finally {
    deviceToDelete.value = null
  }
}

const handleSave = async (deviceData) => {
  try {
    console.log('💾 Saving device data:', deviceData)
    console.log('💾 Device commands:', deviceData.commands)
    console.log('💾 Selected device:', selectedDevice.value)
    
    // Check if we're editing (has valid id) or creating (id is null/undefined)
    if (selectedDevice.value?.id && selectedDevice.value.id !== null) {
      await deviceStore.updateDevice(selectedDevice.value.id, deviceData)
    } else {
      await deviceStore.createDevice(deviceData)
    }
    closeForm()
    // Refresh discovery after saving
    if (discoveryRef.value) {
      await discoveryRef.value.refresh()
    }
  } catch (error) {
    // Extract error message from response
    let errorMessage = 'Failed to save device'
    let suggestion = ''
    let details = ''
    
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
      suggestion = error.response.data.suggestion || ''
    } else if (error.message) {
      errorMessage = error.message
    }
    
    // Add technical details
    if (error.response) {
      details = `Status: ${error.response.status}\nURL: ${error.config?.url || 'N/A'}`
    }
    
    // Pass full error object and context
    showError('Failed to Save Device', errorMessage, suggestion, details, error, {
      action: 'save_device',
      deviceData: deviceData,
      isEdit: !!selectedDevice.value?.id
    })
  }
}

const closeForm = () => {
  showCreateForm.value = false
  selectedDevice.value = null
}

const learnCommands = (device) => {
  selectedDevice.value = device
  showCommandLearner.value = true
}

const closeCommandLearner = () => {
  showCommandLearner.value = false
  selectedDevice.value = null
}

const showError = (title, message, suggestion = '', details = '', error = null, context = {}) => {
  errorDialog.value = {
    title,
    message,
    suggestion,
    details,
    error,
    context
  }
  showErrorDialog.value = true
}

const closeErrorDialog = () => {
  showErrorDialog.value = false
}

const closeGenerationResultDialog = () => {
  showGenerationResultDialog.value = false
}

const handleCommandLearned = async (updateData) => {
  // Optimistically update the device in the store immediately
  // This prevents UI lag while waiting for storage file updates (which can take 10+ seconds in standalone mode)
  if (updateData && updateData.commands && selectedDevice.value) {
    const deviceIndex = deviceStore.devices.findIndex(d => d.id === selectedDevice.value.id)
    if (deviceIndex !== -1) {
      // Update the device's commands in the store
      deviceStore.devices[deviceIndex].commands = updateData.commands
      console.log(`Optimistically updated device ${selectedDevice.value.id} with new command: ${updateData.commandName}`)
    }
  }
  
  // Still reload devices in the background to sync with storage
  // But don't await it - let it happen asynchronously
  deviceStore.loadDevices()
  
  // Refresh discovery to update untracked devices
  if (discoveryRef.value) {
    discoveryRef.value.refresh()
  }
}

const convertStorageNameToDisplay = (storageName) => {
  // Convert snake_case to Title Case with possessive handling
  // e.g., "tony_s_office" -> "Tony's Office", "living_room_tv" -> "Living Room TV"
  const parts = storageName.split('_')
  const result = []
  
  for (let i = 0; i < parts.length; i++) {
    const word = parts[i]
    const nextWord = parts[i + 1]
    
    // Check if this is a possessive pattern (word_s_nextword)
    if (word && nextWord === 's' && parts[i + 2]) {
      // Combine as possessive: "tony_s_office" -> "Tony's Office"
      result.push(word.charAt(0).toUpperCase() + word.slice(1) + "'s")
      i++ // Skip the 's' part
    } else if (word !== 's') {
      // Normal word
      result.push(word.charAt(0).toUpperCase() + word.slice(1))
    }
  }
  
  return result.join(' ')
}

const detectEntityType = (deviceName, commands) => {
  const name = deviceName.toLowerCase()
  const cmdList = commands.map(c => c.toLowerCase())
  
  // Check device name keywords
  if (name.includes('lamp') || name.includes('light')) return 'light'
  if (name.includes('fan')) return 'fan'
  if (name.includes('tv') || name.includes('stereo') || name.includes('speaker') || name.includes('receiver')) return 'media_player'
  if (name.includes('blind') || name.includes('curtain') || name.includes('shade') || name.includes('garage')) return 'cover'
  
  // Check commands for patterns
  const hasMediaCommands = cmdList.some(c => 
    c.includes('volume') || c.includes('channel') || c.includes('play') || c.includes('pause') || c.includes('mute')
  )
  if (hasMediaCommands) return 'media_player'
  
  const hasFanCommands = cmdList.some(c => c.includes('fan_speed') || c.includes('fan_low') || c.includes('fan_high'))
  if (hasFanCommands) return 'fan'
  
  const hasCoverCommands = cmdList.some(c => c.includes('open') || c.includes('close') || c.includes('stop'))
  if (hasCoverCommands) return 'cover'
  
  // Default to switch
  return 'switch'
}

const detectIcon = (deviceName, entityType) => {
  const name = deviceName.toLowerCase()
  
  // Specific device type icons
  if (name.includes('tv')) return 'mdi:television'
  if (name.includes('stereo') || name.includes('receiver')) return 'mdi:speaker'
  if (name.includes('speaker')) return 'mdi:speaker'
  if (name.includes('lamp')) return 'mdi:lamp'
  if (name.includes('light')) return 'mdi:lightbulb'
  if (name.includes('fan')) return 'mdi:fan'
  if (name.includes('blind')) return 'mdi:blinds'
  if (name.includes('curtain')) return 'mdi:curtains'
  if (name.includes('garage')) return 'mdi:garage'
  
  // Default icons by entity type
  const typeIcons = {
    light: 'mdi:lightbulb',
    fan: 'mdi:fan',
    switch: 'mdi:light-switch',
    media_player: 'mdi:speaker',
    cover: 'mdi:window-shutter'
  }
  
  return typeIcons[entityType] || 'mdi:devices'
}

const detectAreaFromName = (deviceName) => {
  // Try to detect area from device name
  // Common patterns: "living_room_tv", "master_bedroom_fan", "tony_s_office"
  const parts = deviceName.toLowerCase().split('_')
  
  // Check for possessive patterns (name_s_room) - e.g., "tony_s_office"
  for (let i = 0; i < parts.length - 2; i++) {
    if (parts[i + 1] === 's') {
      // Found possessive pattern - extract just name_s_room (don't extend further)
      // e.g., "tony_s_office_workbench_lamp" -> "tony_s_office"
      const areaParts = parts.slice(i, i + 3) // name, s, room
      const areaName = convertStorageNameToDisplay(areaParts.join('_'))
      console.log('Detected possessive area:', areaName, 'from', deviceName)
      return areaName
    }
  }
  
  // Common area patterns (two-word areas)
  const twoWordAreas = [
    ['living', 'room'],
    ['dining', 'room'],
    ['master', 'bedroom'],
    ['guest', 'bedroom'],
    ['family', 'room'],
    ['laundry', 'room'],
    ['home', 'office']
  ]
  
  // Check for two-word areas
  for (let i = 0; i < parts.length - 1; i++) {
    const twoWord = [parts[i], parts[i + 1]]
    const match = twoWordAreas.find(area => 
      area[0] === twoWord[0] && area[1] === twoWord[1]
    )
    if (match) {
      return convertStorageNameToDisplay(match.join('_'))
    }
  }
  
  // Check for single-word areas (kitchen, bedroom, garage, etc.)
  const commonAreas = ['kitchen', 'bedroom', 'bathroom', 'garage', 'office', 
                       'basement', 'attic', 'hallway', 'entryway', 'patio', 
                       'deck', 'yard', 'garden']
  
  for (const part of parts) {
    if (commonAreas.includes(part)) {
      return part.charAt(0).toUpperCase() + part.slice(1)
    }
  }
  
  return '' // No area detected
}

const isDeviceType = (word) => {
  // Common device type words that indicate the end of an area name
  const deviceTypes = ['lamp', 'light', 'fan', 'tv', 'stereo', 'speaker', 
                       'switch', 'outlet', 'plug', 'heater', 'ac', 'thermostat',
                       'blind', 'curtain', 'shade', 'door', 'lock', 'camera']
  return deviceTypes.includes(word)
}

const adoptDevice = async (discoveredDevice) => {
  // Convert storage name to display name
  const displayName = convertStorageNameToDisplay(discoveredDevice.device_name)
  
  // Try to detect area from device name
  const detectedArea = detectAreaFromName(discoveredDevice.device_name)
  
  // Detect entity type and icon from device name and commands
  const detectedType = detectEntityType(discoveredDevice.device_name, discoveredDevice.commands)
  const detectedIcon = detectIcon(discoveredDevice.device_name, detectedType)
  
  // Find which Broadlink device owns these commands
  let broadlinkEntity = ''
  try {
    console.log('Finding Broadlink owner for:', discoveredDevice.device_name)
    const response = await api.post('/api/devices/find-broadlink-owner', {
      device_name: discoveredDevice.device_name
    })
    console.log('Broadlink owner response:', response.data)
    broadlinkEntity = response.data.broadlink_entity || ''
    console.log('Detected Broadlink entity:', broadlinkEntity)
  } catch (error) {
    console.error('Error finding Broadlink owner:', error)
  }
  
  // Pre-populate form with discovered device data
  selectedDevice.value = {
    id: null, // New device
    device: discoveredDevice.device_name, // Keep original storage name
    name: displayName, // Display name for user
    entity_type: detectedType, // Auto-detected type
    commands: {},
    area: detectedArea, // Pre-select detected area
    icon: detectedIcon, // Auto-detected icon
    broadlink_entity: broadlinkEntity, // Auto-detected Broadlink device
    enabled: true
  }
  
  // Import commands automatically
  const commandMapping = {}
  discoveredDevice.commands.forEach(cmd => {
    commandMapping[cmd] = cmd
  })
  selectedDevice.value.commands = commandMapping
  
  showCreateForm.value = true
}

const syncAllAreas = async () => {
  syncingAreas.value = true
  try {
    await deviceStore.syncAllAreas()
    toast.success('Areas synced from Home Assistant')
  } catch (error) {
    console.error('Error syncing areas:', error)
    toast.error('Failed to sync areas')
  } finally {
    syncingAreas.value = false
  }
}

const generateEntities = async () => {
  generatingEntities.value = true
  try {
    const response = await api.post('/api/entities/generate', {})
    
    if (response.data.success) {
      // Build detailed success message
      const broadlinkCount = response.data.broadlink_count || 0
      const smartirCount = response.data.smartir_count || 0
      const totalCount = response.data.total_count || 0
      const errors = response.data.errors || []
      
      let title = '✅ Entity Generation Successful'
      let messageParts = []
      
      // Summary
      const summaryParts = []
      if (broadlinkCount > 0) {
        summaryParts.push(`${broadlinkCount} Broadlink native`)
      }
      if (smartirCount > 0) {
        summaryParts.push(`${smartirCount} SmartIR`)
      }
      
      if (summaryParts.length > 0) {
        messageParts.push(`Generated ${summaryParts.join(' and ')} entity configuration${totalCount !== 1 ? 's' : ''}.`)
      }
      
      // File locations
      if (broadlinkCount > 0) {
        messageParts.push('\n📁 Broadlink entities created in:')
        messageParts.push('  • broadlink_manager/entities.yaml')
        messageParts.push('  • broadlink_manager/helpers.yaml')
      }
      
      if (smartirCount > 0) {
        messageParts.push('\n📁 SmartIR entities created in:')
        messageParts.push('  • smartir/climate.yaml')
        messageParts.push('  • smartir/media_player.yaml')
        messageParts.push('  • smartir/fan.yaml')
      }
      
      // Configuration instructions
      messageParts.push('\n📝 Next steps:')
      messageParts.push('1. Check your configuration.yaml includes the generated files')
      messageParts.push('2. Restart Home Assistant to load the new entities')
      
      // Show errors if any
      if (errors.length > 0) {
        title = '⚠️ Entity Generation Completed with Errors'
        messageParts.push(`\n⚠️ ${errors.length} error${errors.length !== 1 ? 's' : ''} occurred:`)
        errors.forEach(err => {
          messageParts.push(`  • ${err}`)
        })
      }
      
      generationResult.value = {
        success: true,
        title: title,
        message: messageParts.join('\n')
      }
      showGenerationResultDialog.value = true
      
    } else {
      // Show failure dialog
      generationResult.value = {
        success: false,
        title: '❌ Entity Generation Failed',
        message: response.data.message || 'Failed to generate entities.\n\nPlease check that you have at least one device configured.'
      }
      showGenerationResultDialog.value = true
    }
  } catch (error) {
    console.error('Error generating entities:', error)
    const errorMsg = error.response?.data?.error || error.message || 'Unknown error occurred'
    
    generationResult.value = {
      success: false,
      title: '❌ Entity Generation Error',
      message: `Failed to generate entities:\n\n${errorMsg}\n\nPlease check the logs for more details.`
    }
    showGenerationResultDialog.value = true
  } finally {
    generatingEntities.value = false
  }
}

const handleSendCommand = async ({ device, command }) => {
  try {
    const payload = {
      device_id: device.id,
      command: command,
      entity_id: device.broadlink_entity,
      device: device.device
    }
    await api.post('/api/commands/test', payload)
    toast.success(`Sent ${command} to ${device.name}`)
  } catch (error) {
    console.error('Error sending command:', error)
    const errorMsg = error.response?.data?.error || error.message || 'Unknown error'
    toast.error(`Failed to send ${command}: ${errorMsg}`)
  }
}
</script>

<style scoped>
.device-list-card {
  background: var(--ha-card-background);
  border-radius: 8px;
  border: 1px solid var(--ha-border-color);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--ha-border-color);
  background: rgba(3, 169, 244, 0.12);
  transition: background 0.2s;
  user-select: none;
  gap: 12px;
}

.card-header:hover {
  background: rgba(3, 169, 244, 0.18);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  cursor: pointer;
}

.header-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(var(--ha-primary-rgb), 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon i {
  font-size: 24px;
  color: var(--ha-primary-color);
}

.header-left h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.header-badges {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 8px;
}

.header-info {
  font-size: 13px;
  color: var(--secondary-text-color);
  padding: 4px 8px;
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
  border-radius: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-button {
  background: transparent;
  border: none;
  color: var(--ha-text-secondary-color);
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.icon-button:hover {
  background: var(--ha-hover-color);
  color: var(--ha-text-primary-color);
}

.icon-button i {
  font-size: 20px;
}

.chevron-button {
  pointer-events: none;
}

.device-count {
  background: var(--ha-primary-color);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
}

.card-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: rgba(var(--ha-primary-rgb), 0.03);
  border-radius: 8px;
  border: 1px solid var(--ha-border-color);
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-row-search {
  width: 100%;
}

.filter-row-dropdowns {
  width: 100%;
}

.filter-group {
  flex: 1;
  min-width: 200px;
}

.filter-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ha-text-secondary-color);
}

.filter-group i {
  font-size: 18px;
  color: var(--ha-primary-color);
}

.filter-group select {
  flex: 1;
  padding: 8px 12px;
  background: var(--ha-surface-color);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-group select:hover {
  border-color: var(--ha-primary-color);
}

.filter-group select:focus {
  outline: none;
  border-color: var(--ha-primary-color);
  box-shadow: 0 0 0 3px rgba(var(--ha-primary-rgb), 0.1);
}

.filter-search {
  flex: 1;
  width: 100%;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  background: var(--ha-surface-color);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: var(--ha-text-secondary-color);
  opacity: 0.7;
}

.search-input:hover {
  border-color: var(--ha-primary-color);
}

.search-input:focus {
  outline: none;
  border-color: var(--ha-primary-color);
  box-shadow: 0 0 0 3px rgba(var(--ha-primary-rgb), 0.1);
}

.filter-toggle label {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.toggle-buttons {
  display: flex;
  gap: 4px;
  width: 100%;
}

.toggle-btn {
  flex: 1;
  padding: 8px 12px;
  background: var(--ha-surface-color);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  color: var(--ha-text-secondary-color);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  white-space: nowrap;
}

.toggle-btn:hover {
  border-color: var(--ha-primary-color);
  background: var(--ha-hover-color);
}

.toggle-btn.active {
  background: var(--ha-primary-color);
  border-color: var(--ha-primary-color);
  color: white;
  font-weight: 600;
}

.toggle-btn i {
  font-size: 16px;
}

.btn-clear-filters {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  color: var(--ha-text-secondary-color);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-clear-filters:hover {
  background: var(--ha-error-color);
  color: white;
  border-color: var(--ha-error-color);
}

/* View Toggle Button Group */
.view-toggle-group {
  display: flex;
  gap: 0;
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--ha-surface-color);
}

.view-toggle-btn {
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-right: 1px solid var(--ha-border-color);
  color: var(--ha-text-secondary-color);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  font-weight: 500;
}

.view-toggle-btn:last-child {
  border-right: none;
}

.view-toggle-btn:hover:not(.active) {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
  color: var(--ha-text-primary-color);
}

.view-toggle-btn.active {
  background: var(--ha-primary-color);
  color: white;
  font-weight: 600;
}

.view-toggle-btn i {
  font-size: 16px;
}

.filter-results {
  margin-left: 12px;
  padding: 8px 12px;
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
  border-radius: 6px;
  font-size: 13px;
  color: var(--ha-text-secondary-color);
  font-weight: 500;
  white-space: nowrap;
}

.no-results {
  text-align: center;
  padding: 48px 24px;
  color: var(--ha-text-secondary-color);
}

.no-results i {
  font-size: 64px;
  color: var(--ha-text-secondary-color);
  opacity: 0.5;
  margin-bottom: 16px;
}

.no-results h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: var(--ha-text-primary-color);
  font-weight: 500;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 32px;
  background: var(--ha-card-background);
  border-radius: 12px;
  border: 1px solid var(--ha-border-color);
}

.loading-state i {
  font-size: 48px;
  color: var(--ha-primary-color);
  margin-bottom: 16px;
}

.loading-state p {
  color: var(--ha-text-secondary-color);
  font-size: 16px;
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4px 12px;
  background: rgba(var(--ha-error-rgb), 0.1);
  color: var(--ha-error-color);
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.error-state i {
  font-size: 48px;
  color: var(--ha-error-color);
  margin-bottom: 16px;
}

.error-state p {
  color: var(--ha-text-primary-color);
  font-size: 16px;
  margin-bottom: 16px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--ha-text-secondary-color);
}

.empty-state i {
  font-size: 64px;
  opacity: 0.3;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--ha-text-primary-color);
}

.empty-state p {
  margin: 0 0 24px 0;
  font-size: 14px;
}

/* Device Grid */
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

@media (max-width: 768px) {
  .device-list-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .device-grid {
    grid-template-columns: 1fr;
  }
}

/* Toggle Switch Styles */
.filter-toggle {
  display: flex;
  align-items: center;
  min-width: fit-content;
}

.toggle-label {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  gap: 12px !important;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.toggle-checkbox {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  background: var(--ha-border-color);
  border-radius: 24px;
  transition: background 0.3s;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: transform 0.3s;
}

.toggle-checkbox:checked + .toggle-slider {
  background: var(--ha-primary-color);
}

.toggle-checkbox:checked + .toggle-slider::before {
  transform: translateX(20px);
}

.toggle-checkbox:focus + .toggle-slider {
  box-shadow: 0 0 0 3px rgba(var(--ha-primary-rgb), 0.2);
}

.toggle-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
  white-space: nowrap;
}

.smartir-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

/* ===== Mobile Responsive Styles ===== */
@media (max-width: 767px) {
  /* Card header adjustments */
  .card-header {
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px;
  }

  .header-left {
    flex: 1;
    min-width: 0;
  }

  .header-right {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .header-right .btn {
    width: 100%;
    justify-content: center;
  }

  /* Filter bar mobile layout */
  .filter-bar {
    padding: 12px;
    gap: 12px;
  }

  .filter-row {
    gap: 8px;
  }

  .filter-row-search {
    margin-bottom: 8px;
  }

  .filter-search {
    width: 100%;
  }

  .filter-search input {
    width: 100%;
  }

  .filter-row-dropdowns {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    width: 100%;
    min-width: unset;
  }

  .filter-group select {
    width: 100%;
  }

  .btn-clear-filters {
    width: 100%;
    justify-content: center;
  }

  .filter-results {
    width: 100%;
    text-align: center;
    margin-left: 0;
  }

  /* Device grid - single column on mobile */
  .device-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  /* Increase touch target sizes */
  .btn,
  .icon-button {
    min-height: 44px;
    min-width: 44px;
  }

  .view-toggle-btn {
    min-height: 44px;
    padding: 10px 16px;
  }

  /* Card body padding */
  .card-body {
    padding: 12px;
  }

  /* Empty/Error/Loading states */
  .empty-state,
  .error-state,
  .loading-state {
    padding: 40px 16px;
  }

  /* Header badges - stack on very small screens */
  @media (max-width: 400px) {
    .header-badges {
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }
  }
}

/* Tablet adjustments */
@media (min-width: 768px) and (max-width: 1023px) {
  .device-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }

  .filter-row-dropdowns {
    flex-wrap: wrap;
  }

  .filter-group {
    min-width: 200px;
  }
}
</style>
