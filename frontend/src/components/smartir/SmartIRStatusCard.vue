<template>
  <div class="smartir-status-card">
    <div class="card-header">
      <button class="icon-button chevron-button" @click="isExpanded = !isExpanded">
        <i class="mdi" :class="isExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down'"></i>
      </button>
      <div class="header-left" @click="isExpanded = !isExpanded">
        <img :src="smartirLogo" alt="SmartIR" class="smartir-logo" />
        <h3>SmartIR Integration</h3>
        
        <!-- Compact Status Info -->
        <div class="header-badges">
          <!-- Always show simulation toggle pill -->
          <div 
            class="simulation-toggle-pill" 
            :class="{ active: simulatingNotInstalled }"
            @click.stop="toggleInstallSimulation"
            :title="simulatingNotInstalled ? 'Click to show as installed' : 'Click to simulate not-installed'"
          >
            <i class="mdi" :class="simulatingNotInstalled ? 'mdi-eye-off' : 'mdi-eye'"></i>
            <span>{{ simulatingNotInstalled ? 'Simulating: Not Installed' : 'Simulation Mode' }}</span>
          </div>
          
          <!-- Status badges (only when showing as installed) -->
          <template v-if="displayStatus?.installed">
            <div class="status-badge-mini success">
              <i class="mdi mdi-check-circle"></i>
              <span>Installed</span>
            </div>
            <span class="header-info">v{{ displayStatus.version || 'Unknown' }}</span>
            <span class="header-info">{{ platformCount }} platform{{ platformCount !== 1 ? 's' : '' }}</span>
            <span class="header-info">{{ totalDevices }} device{{ totalDevices !== 1 ? 's' : '' }}</span>
          </template>
        </div>
      </div>
      <div class="header-right">
        <button 
          v-if="status?.installed && isExpanded" 
          @click.stop="showHelp = !showHelp" 
          class="icon-button"
          :class="{ active: showHelp }"
          title="Show help"
        >
          <i class="mdi mdi-help-circle"></i>
        </button>
        <button 
          v-if="status?.installed && isExpanded" 
          @click.stop="refreshStatus" 
          class="icon-button"
          title="Refresh status"
        >
          <i class="mdi mdi-refresh"></i>
        </button>
        <button 
          v-if="status?.installed && isExpanded" 
          @click.stop="openCodeTester" 
          class="btn btn-secondary"
        >
          <i class="mdi mdi-test-tube"></i>
          Test Codes
        </button>
        <button 
          v-if="status?.installed && isExpanded" 
          @click.stop="createProfile" 
          class="btn btn-primary"
        >
          <i class="mdi mdi-plus"></i>
          Create SmartIR Profile
        </button>
      </div>
    </div>

    <div v-show="isExpanded">
      <!-- Loading State -->
      <div v-if="loading" class="card-body loading-state">
        <div class="spinner"></div>
        <p>Checking SmartIR installation...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="card-body error-state">
        <i class="mdi mdi-alert-circle"></i>
        <p>{{ error }}</p>
        <button @click="refreshStatus" class="btn-secondary">
          Try Again
        </button>
      </div>

      <!-- SmartIR Installed -->
      <div v-else-if="displayStatus?.installed" class="card-body installed-state">
      <!-- Help Panel (Collapsible) -->
      <div v-if="showHelp" class="help-panel">
        <div v-if="status.recommendation" class="recommendation">
          <p>{{ status.recommendation.message }}</p>
          <div v-if="status.recommendation.next_steps" class="next-steps">
            <strong>Next Steps:</strong>
            <ul>
              <li v-for="(step, index) in status.recommendation.next_steps" :key="index">
                {{ step }}
              </li>
            </ul>
          </div>
        </div>
        <div class="help-actions">
          <button @click="viewDocumentation" class="btn-secondary">
            <i class="mdi mdi-book-open-variant"></i>
            View Documentation
          </button>
        </div>
      </div>

      <!-- Filter Bar -->
      <div v-if="allProfiles.length > 0 && !simulatingNotInstalled" class="filter-bar">
        <div class="filter-row">
          <div class="filter-group filter-search">
            <label>
              <i class="mdi mdi-magnify"></i>
              <input
                v-model="filters.search"
                type="text"
                placeholder="Search profiles..."
                class="search-input"
              />
            </label>
          </div>

          <div class="filter-group">
            <label>
              <i class="mdi mdi-shape"></i>
              <select v-model="filters.platform">
                <option value="">All Platforms</option>
                <option value="climate">Climate</option>
                <option value="media_player">Media Player</option>
                <option value="fan">Fan</option>
                <option value="light">Light</option>
              </select>
            </label>
          </div>

          <button v-if="hasActiveFilters" @click="clearFilters" class="btn-clear-filters">
            <i class="mdi mdi-filter-remove"></i>
            Clear
          </button>

          <div class="filter-results">
            {{ filteredProfiles.length }} of {{ allProfiles.length }}
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loadingAllProfiles" class="loading-state">
        <i class="mdi mdi-loading mdi-spin"></i>
        <p>Loading profiles...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="allProfiles.length === 0" class="empty-state">
        <i class="mdi mdi-file-document-outline"></i>
        <h3>No Profiles Yet</h3>
        <p>Create your first SmartIR profile to get started</p>
      </div>

      <!-- Profile Cards Grid -->
      <div v-else-if="!simulatingNotInstalled" class="profiles-grid">
        <SmartIRProfileCard
          v-for="profile in filteredProfiles"
          :key="`${profile.platform}-${profile.code}`"
          :profile="profile"
          @edit="editProfile(profile.platform, profile)"
          @commands="editProfile(profile.platform, profile, 2)"
          @download="downloadProfile(profile.platform, profile)"
          @delete="deleteProfile(profile.platform, profile)"
        />
      </div>

      <!-- No Results -->
      <div v-if="allProfiles.length > 0 && filteredProfiles.length === 0 && !simulatingNotInstalled" class="no-results">
        <i class="mdi mdi-filter-off"></i>
        <h3>No profiles match your filters</h3>
        <p>Try adjusting your search or filter criteria</p>
      </div>

    </div>

    <!-- SmartIR Not Installed -->
    <div v-else class="card-body not-installed-state">
      <div class="status-badge warning">
        <i class="mdi mdi-information"></i>
        <span>Not Installed</span>
      </div>

      <div class="benefits-section">
        <h4>Why Install SmartIR?</h4>
        <ul class="benefits-list">
          <li v-for="(benefit, index) in status?.recommendation?.benefits || defaultBenefits" :key="index">
            <i class="mdi mdi-check"></i>
            <span>{{ benefit }}</span>
          </li>
        </ul>
      </div>

      <div class="recommendation">
        <p>{{ status?.recommendation?.message || 'Install SmartIR to unlock climate device support!' }}</p>
      </div>

      <div class="card-actions">
        <button @click="showInstallGuide" class="btn-primary">
          <i class="mdi mdi-download"></i>
          Install SmartIR
        </button>
        <button @click="openSmartIRGitHub" class="btn-secondary">
          <i class="mdi mdi-github"></i>
          View on GitHub
        </button>
        <button @click="viewDocumentation" class="btn-secondary">
          <i class="mdi mdi-help-circle"></i>
          Learn More
        </button>
      </div>
    </div>
    </div>

    <!-- Confirm Delete Dialog -->
    <ConfirmDialog
      :isOpen="confirmDelete.show"
      :title="confirmDelete.title"
      :message="confirmDelete.message"
      confirmText="Delete"
      cancelText="Cancel"
      :dangerMode="true"
      @confirm="handleDeleteConfirm"
      @cancel="confirmDelete.show = false"
    />

    <!-- Code Tester Modal -->
    <SmartIRCodeTester
      :isOpen="showCodeTester"
      @close="showCodeTester = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, watch, nextTick } from 'vue'
import { smartirService } from '../../services/smartir'
import ConfirmDialog from '../common/ConfirmDialog.vue'
import SmartIRProfileCard from './SmartIRProfileCard.vue'
import SmartIRCodeTester from './SmartIRCodeTester.vue'
import smartirLogo from '@/assets/images/smartir-logo.png'

const emit = defineEmits(['create-profile', 'show-install-guide', 'edit-profile'])

// Inject SmartIR status from App.vue
const smartirStatus = inject('smartirStatus')
const smartirEnabled = inject('smartirEnabled')
const refreshSmartIR = inject('refreshSmartIR')

const loading = ref(false)
const error = ref(null)
const status = ref(smartirStatus?.value || null)
// Load simulation state from localStorage
const simulatingNotInstalled = ref(localStorage.getItem('smartir_simulate_not_installed') === 'true')
const showHelp = ref(false)
const isExpanded = ref(true)
const allProfiles = ref([])
const loadingAllProfiles = ref(false)
const filters = ref({
  search: '',
  platform: ''
})
const confirmDelete = ref({
  show: false,
  title: '',
  message: '',
  platform: null,
  profile: null
})
const showCodeTester = ref(false)

const defaultBenefits = [
  'Full climate entity support (AC, heaters)',
  '120+ pre-configured device profiles',
  'Temperature and humidity sensor integration',
  'HVAC mode control (heat, cool, auto, dry, fan)'
]

// All supported SmartIR platforms
const allPlatforms = ['climate', 'media_player', 'fan', 'light']

// Display status that can be toggled for simulation
const displayStatus = computed(() => {
  if (simulatingNotInstalled.value) {
    return {
      installed: false,
      recommendation: {
        message: 'Install SmartIR to unlock climate device support!',
        benefits: [
          'Full climate entity support (AC, heaters)',
          '120+ pre-configured device profiles',
          'Temperature and humidity sensor integration',
          'HVAC mode control (heat, cool, auto, dry, fan)'
        ]
      }
    }
  }
  return status.value
})

const platformCount = computed(() => {
  return displayStatus.value?.platforms?.length || 0
})

const totalDevices = computed(() => {
  if (!displayStatus.value?.device_counts) return 0
  return Object.values(displayStatus.value.device_counts).reduce((sum, count) => sum + count, 0)
})

function toggleInstallSimulation() {
  simulatingNotInstalled.value = !simulatingNotInstalled.value
  // Persist to localStorage
  localStorage.setItem('smartir_simulate_not_installed', simulatingNotInstalled.value.toString())
  
  // Reload profiles when toggling back to installed
  if (!simulatingNotInstalled.value && status.value?.installed) {
    loadAllProfiles()
  }
}

const filteredProfiles = computed(() => {
  let profiles = allProfiles.value

  // Text search
  if (filters.value.search) {
    const searchLower = filters.value.search.toLowerCase()
    profiles = profiles.filter(p => {
      return (
        p.manufacturer?.toLowerCase().includes(searchLower) ||
        p.model?.toLowerCase().includes(searchLower) ||
        p.code?.toString().includes(searchLower) ||
        p.platform?.toLowerCase().includes(searchLower)
      )
    })
  }

  // Platform filter
  if (filters.value.platform) {
    profiles = profiles.filter(p => p.platform === filters.value.platform)
  }

  return profiles
})

const hasActiveFilters = computed(() => {
  return filters.value.search || filters.value.platform
})

function clearFilters() {
  filters.value.search = ''
  filters.value.platform = ''
}

function getPlatformIcon(platform) {
  const icons = {
    'climate': 'mdi mdi-air-conditioner',
    'media_player': 'mdi mdi-television',
    'fan': 'mdi mdi-fan',
    'light': 'mdi mdi-lightbulb'
  }
  return icons[platform] || 'mdi mdi-devices'
}

function formatPlatformName(platform) {
  return platform
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

async function refreshStatus() {
  loading.value = true
  error.value = null
  
  try {
    if (refreshSmartIR) {
      await refreshSmartIR()
    } else {
      const newStatus = await smartirService.getStatus()
      status.value = newStatus
    }
  } catch (err) {
    error.value = err.message || 'Failed to refresh SmartIR status'
    console.error('Error refreshing SmartIR status:', err)
  } finally {
    loading.value = false
  }
}

function createProfile() {
  emit('create-profile')
}

function openCodeTester() {
  showCodeTester.value = true
}

function showInstallGuide() {
  emit('show-install-guide')
}

function viewDocumentation() {
  window.open('https://github.com/smartHomeHub/SmartIR', '_blank')
}

function openSmartIRGitHub() {
  window.open('https://github.com/smartHomeHub/SmartIR', '_blank')
}

async function loadAllProfiles() {
  loadingAllProfiles.value = true
  const allProfilesData = []
  
  try {
    // Load profiles from all platforms
    for (const platform of allPlatforms) {
      try {
        const response = await fetch(`api/smartir/platforms/${platform}/profiles`)
        if (response.ok) {
          const data = await response.json()
          const platformProfiles = (data.profiles || []).map(p => ({
            ...p,
            platform
          }))
          allProfilesData.push(...platformProfiles)
        }
      } catch (err) {
        console.error(`Error loading ${platform} profiles:`, err)
      }
    }
    
    allProfiles.value = allProfilesData
  } finally {
    loadingAllProfiles.value = false
  }
}

function editProfile(platform, profile, startStep) {
  emit('edit-profile', { platform, profile, startStep })
}

async function downloadProfile(platform, profile) {
  try {
    // Fetch the full profile JSON
    const response = await fetch(`api/smartir/platforms/${platform}/profiles/${profile.code}`)
    if (!response.ok) {
      throw new Error('Failed to fetch profile')
    }
    
    const data = await response.json()
    
    // Create blob and download
    const jsonString = JSON.stringify(data.profile, null, 2)
    const blob = new Blob([jsonString], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `smartir_${platform}_${profile.manufacturer}_${profile.model}_${profile.code}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    const toastRef = inject('toast')
    toastRef.value?.success(`Downloaded ${profile.manufacturer} ${profile.model}`, '✅ Profile Downloaded')
  } catch (err) {
    console.error('Error downloading profile:', err)
    const toastRef = inject('toast')
    toastRef.value?.error('Failed to download profile', '❌ Download Error')
  }
}

function deleteProfile(platform, profile) {
  // Show confirmation dialog
  confirmDelete.value = {
    show: true,
    title: `Delete ${profile.manufacturer} ${profile.model}?`,
    message: `Device Code: ${profile.code}\n\nThis will remove the profile and update your configuration.`,
    platform,
    profile
  }
}

async function handleDeleteConfirm() {
  const toastRef = inject('toast')
  const { platform, profile } = confirmDelete.value
  
  // Close dialog
  confirmDelete.value.show = false
  
  try {
    const response = await fetch(`api/smartir/profiles/${profile.code}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform })
    })
    
    if (response.ok) {
      // Reload all profiles
      await loadAllProfiles()
      
      // Wait for DOM update
      await nextTick()
      
      // Then refresh status
      await refreshStatus()
      
      // Show success toast after everything is updated
      toastRef.value?.success(
        `${profile.manufacturer} ${profile.model} has been removed`,
        '✅ Profile Deleted'
      )
    } else {
      const error = await response.json()
      toastRef.value?.error(error.error || 'Unknown error', '❌ Delete Failed')
    }
  } catch (err) {
    console.error('Error deleting profile:', err)
    toastRef.value?.error('Failed to delete profile', '❌ Delete Error')
  }
}

// Watch for changes in injected status
watch(smartirStatus, (newStatus) => {
  if (newStatus) {
    status.value = newStatus
  }
}, { immediate: true })

onMounted(async () => {
  // Try to use injected status first
  if (smartirStatus?.value) {
    status.value = smartirStatus.value
  }
  
  // If no injected status available, fetch directly
  if (!status.value) {
    await refreshStatus()
  }
  
  // Load all profiles if SmartIR is installed
  if (status.value?.installed) {
    await loadAllProfiles()
  }
})

// Expose methods for parent components
defineExpose({
  loadAllProfiles,
  refreshStatus
})
</script>

<style scoped>
.smartir-status-card {
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

.chevron-button {
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
  cursor: pointer;
}

.header-left i {
  font-size: 24px;
  color: var(--primary-color);
}

.smartir-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.header-badges {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 8px;
}

.status-badge-mini {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 12px;
}

.status-badge-mini.success {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.status-badge-mini i {
  font-size: 14px;
}

/* Simulation Toggle Pill */
.simulation-toggle-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  font-weight: 600;
  font-size: 12px;
  background: rgba(var(--ha-text-secondary-rgb, 128, 128, 128), 0.1);
  color: var(--ha-text-secondary-color);
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.simulation-toggle-pill:hover {
  background: rgba(var(--ha-text-secondary-rgb, 128, 128, 128), 0.2);
  transform: scale(1.05);
}

.simulation-toggle-pill.active {
  background: rgba(255, 152, 0, 0.15);
  color: #ff9800;
  border-color: rgba(255, 152, 0, 0.3);
  animation: pulse-warning 2s ease-in-out infinite;
}

.simulation-toggle-pill i {
  font-size: 14px;
}

@keyframes pulse-warning {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.02);
  }
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
  gap: 8px;
}

.icon-button {
  background: transparent;
  border: none;
  color: var(--primary-text-color);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.icon-button:hover {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
}

.icon-button.active {
  background: var(--ha-primary-color);
  color: white;
}

.icon-button i {
  font-size: 20px;
}

.card-body {
  padding: 20px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 200px;
  color: var(--secondary-text-color);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--ha-border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  color: var(--error-color);
}

.error-state i {
  font-size: 48px;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 20px;
}

.status-badge.success {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.status-badge.warning {
  background: rgba(255, 152, 0, 0.1);
  color: #ff9800;
}

.status-badge i {
  font-size: 18px;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  color: var(--secondary-text-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item .value {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-text-color);
}

/* Filter Bar */
.filter-bar {
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

.filter-group {
  flex: 0 0 auto;
  min-width: 200px;
}

.filter-search {
  flex: 1;
  min-width: 300px;
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

.btn-clear-filters {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--ha-border-color);
  border-radius: 6px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-clear-filters:hover {
  background: var(--ha-error-color);
  color: white;
  border-color: var(--ha-error-color);
}

.filter-results {
  margin-left: auto;
  padding: 8px 12px;
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
  border-radius: 6px;
  font-size: 13px;
  color: var(--ha-text-secondary-color);
  font-weight: 500;
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
  margin: 0;
  font-size: 14px;
}

/* No Results */
.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--ha-text-secondary-color);
}

.no-results i {
  font-size: 64px;
  opacity: 0.3;
  margin-bottom: 16px;
}

.no-results h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--ha-text-primary-color);
}

.no-results p {
  margin: 0;
  font-size: 14px;
}

/* Profiles Grid */
.profiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.profile-card {
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.2s;
  min-height: 120px;
}

.profile-card:hover {
  box-shadow: var(--ha-shadow-md);
  border-color: var(--ha-primary-color);
}

.profile-card-header {
  display: flex;
  gap: 12px;
  flex: 1;
}

.profile-icon {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1);
  border-radius: 8px;
}

.profile-icon i {
  font-size: 24px;
  color: var(--ha-primary-color);
}

.profile-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.profile-details h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: flex-start;
}

.platform-badge,
.code-badge,
.controller-badge,
.command-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.platform-badge {
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1);
  color: var(--ha-primary-color);
}

.platform-badge i {
  font-size: 14px;
}

.code-badge {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
  color: var(--ha-text-secondary-color);
}

.controller-badge {
  background: rgba(255, 152, 0, 0.1);
  color: #ff9800;
}

.controller-badge i {
  font-size: 14px;
}

.command-count {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.command-count.has-learned {
  background: rgba(33, 150, 243, 0.1);
  color: #2196f3;
}

.command-count i {
  font-size: 14px;
}

.learned-indicator {
  font-weight: 600;
  opacity: 0.9;
}

.profile-card-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--ha-border-color);
}

/* Benefits Section */
.benefits-section {
  margin-bottom: 20px;
}

.benefits-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.benefits-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.benefits-list li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  color: var(--primary-text-color);
}

.benefits-list i {
  color: #4caf50;
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

/* Recommendation */
.recommendation {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
  border-left: 4px solid var(--primary-color);
  padding: 16px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.recommendation p {
  margin: 0 0 12px 0;
  color: var(--primary-text-color);
}

.recommendation p:last-child {
  margin-bottom: 0;
}

.next-steps {
  margin-top: 12px;
}

.next-steps strong {
  display: block;
  margin-bottom: 8px;
  color: var(--primary-text-color);
}

.next-steps ul {
  margin: 0;
  padding-left: 20px;
}

.next-steps li {
  margin-bottom: 4px;
  color: var(--primary-text-color);
}

.help-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

/* Card Actions */
.card-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-primary,
.btn-secondary {
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

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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

.btn-primary i,
.btn-secondary i {
  font-size: 18px;
}

/* Help Panel */
.help-panel {
  margin-bottom: 20px;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.action-btn {
  flex: 1;
  background: transparent;
  border: 1px solid var(--ha-border-color);
  color: var(--ha-text-primary-color);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: 14px;
}

.action-btn:hover {
  background: var(--ha-primary-color);
  color: white;
  border-color: var(--ha-primary-color);
}

.action-btn.delete:hover {
  background: var(--ha-error-color, #f44336);
  border-color: var(--ha-error-color, #f44336);
}

.action-btn i {
  font-size: 18px;
}

/* Dark mode adjustments */
:global(.dark-mode) .platform-item {
  background: rgba(255, 255, 255, 0.05);
}

:global(.dark-mode) .recommendation {
  background: rgba(255, 255, 255, 0.05);
}

:global(.dark-mode) .header-info {
  background: rgba(255, 255, 255, 0.05);
}

:global(.dark-mode) .platform-profiles {
  background: rgba(255, 255, 255, 0.02);
}
</style>
