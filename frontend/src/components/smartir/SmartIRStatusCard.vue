<template>
  <div class="smartir-status-card">
    <div class="card-header">
      <div class="header-left">
        <i class="mdi mdi-air-conditioner"></i>
        <h3>SmartIR Integration</h3>
        
        <!-- Compact Status Info -->
        <div v-if="status?.installed" class="header-badges">
          <div class="status-badge-mini success">
            <i class="mdi mdi-check-circle"></i>
            <span>Installed</span>
          </div>
          <span class="header-info">v{{ status.version || 'Unknown' }}</span>
          <span class="header-info">{{ platformCount }} platform{{ platformCount !== 1 ? 's' : '' }}</span>
          <span class="header-info">{{ totalDevices }} device{{ totalDevices !== 1 ? 's' : '' }}</span>
        </div>
      </div>
      <div class="header-right">
        <button 
          v-if="status?.installed" 
          @click="showHelp = !showHelp" 
          class="icon-button"
          :class="{ active: showHelp }"
          title="Show help"
        >
          <i class="mdi mdi-help-circle"></i>
        </button>
        <button 
          v-if="status?.installed" 
          @click="refreshStatus" 
          class="icon-button"
          title="Refresh status"
        >
          <i class="mdi mdi-refresh"></i>
        </button>
      </div>
    </div>

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
    <div v-else-if="status?.installed" class="card-body installed-state">
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
      </div>

      <!-- Platform Details with Profiles -->
      <div v-if="status.platforms?.length" class="platforms-section">
        <h4>Available Platforms</h4>
        <div class="platform-list">
          <div 
            v-for="platform in status.platforms" 
            :key="platform"
            class="platform-card"
            :class="{ expanded: expandedPlatforms[platform] }"
          >
            <div class="platform-header" @click="togglePlatform(platform)">
              <div class="platform-icon">
                <i :class="getPlatformIcon(platform)"></i>
              </div>
              <div class="platform-info">
                <span class="platform-name">{{ formatPlatformName(platform) }}</span>
                <span class="device-count">
                  {{ status.device_counts?.[platform] || 0 }} devices
                </span>
              </div>
              <i class="mdi" :class="expandedPlatforms[platform] ? 'mdi-chevron-up' : 'mdi-chevron-down'"></i>
            </div>
            
            <!-- Expanded Profile List -->
            <div v-if="expandedPlatforms[platform]" class="platform-profiles">
              <div v-if="loadingProfiles[platform]" class="profiles-loading">
                <div class="spinner-small"></div>
                <span>Loading profiles...</span>
              </div>
              <div v-else-if="profiles[platform]?.length" class="profile-list">
                <div 
                  v-for="profile in profiles[platform]" 
                  :key="`${platform}-${profile.code}`"
                  class="profile-item"
                >
                  <div class="profile-info">
                    <span class="profile-name">{{ profile.manufacturer }} {{ profile.model }}</span>
                    <span class="profile-code">Code: {{ profile.code }}</span>
                  </div>
                  <div class="profile-actions">
                    <button @click="editProfile(platform, profile)" class="action-btn" title="Edit">
                      <i class="mdi mdi-pencil"></i>
                    </button>
                    <button @click="downloadProfile(platform, profile)" class="action-btn" title="Download">
                      <i class="mdi mdi-download"></i>
                    </button>
                    <button @click="deleteProfile(platform, profile)" class="action-btn delete" title="Delete">
                      <i class="mdi mdi-delete"></i>
                    </button>
                  </div>
                </div>
              </div>
              <div v-else class="no-profiles">
                <i class="mdi mdi-information-outline"></i>
                <p>No profiles created yet</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="card-actions">
        <button @click="createProfile" class="btn-primary">
          <i class="mdi mdi-plus-circle"></i>
          Create SmartIR Profile
        </button>
        <button @click="viewDocumentation" class="btn-secondary">
          <i class="mdi mdi-book-open-variant"></i>
          Documentation
        </button>
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
        <button @click="viewDocumentation" class="btn-secondary">
          <i class="mdi mdi-help-circle"></i>
          Learn More
        </button>
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
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, watch, nextTick } from 'vue'
import { smartirService } from '../../services/smartir'
import ConfirmDialog from '../common/ConfirmDialog.vue'

const emit = defineEmits(['create-profile', 'show-install-guide', 'edit-profile'])

// Inject SmartIR status from App.vue
const smartirStatus = inject('smartirStatus')
const refreshSmartIR = inject('refreshSmartIR')

const loading = ref(false)
const error = ref(null)
const status = ref(smartirStatus?.value || null)
const showHelp = ref(false)
const expandedPlatforms = ref({})
const profiles = ref({})
const loadingProfiles = ref({})
const confirmDelete = ref({
  show: false,
  title: '',
  message: '',
  platform: null,
  profile: null
})

const defaultBenefits = [
  'Full climate entity support (AC, heaters)',
  '120+ pre-configured device profiles',
  'Temperature and humidity sensor integration',
  'HVAC mode control (heat, cool, auto, dry, fan)'
]

const platformCount = computed(() => {
  return status.value?.platforms?.length || 0
})

const totalDevices = computed(() => {
  if (!status.value?.device_counts) return 0
  return Object.values(status.value.device_counts).reduce((sum, count) => sum + count, 0)
})

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

function showInstallGuide() {
  emit('show-install-guide')
}

function viewDocumentation() {
  window.open('https://github.com/smartHomeHub/SmartIR', '_blank')
}

async function togglePlatform(platform) {
  // Accordion behavior - close all others
  const wasExpanded = expandedPlatforms.value[platform]
  
  // Close all platforms
  Object.keys(expandedPlatforms.value).forEach(key => {
    expandedPlatforms.value[key] = false
  })
  
  // Toggle current platform (opposite of what it was)
  expandedPlatforms.value[platform] = !wasExpanded
  
  // Load profiles if expanding and not already loaded
  if (expandedPlatforms.value[platform] && !profiles.value[platform]) {
    await loadProfiles(platform)
  }
}

async function loadProfiles(platform) {
  loadingProfiles.value[platform] = true
  
  try {
    const response = await fetch(`/api/smartir/platforms/${platform}/profiles`)
    if (response.ok) {
      const data = await response.json()
      // Use Object.assign to ensure reactivity
      profiles.value = {
        ...profiles.value,
        [platform]: data.profiles || []
      }
    }
  } catch (err) {
    console.error(`Error loading ${platform} profiles:`, err)
    profiles.value = {
      ...profiles.value,
      [platform]: []
    }
  } finally {
    loadingProfiles.value[platform] = false
  }
}

function editProfile(platform, profile) {
  // Emit event to open profile builder with this profile data
  emit('edit-profile', { platform, profile })
}

async function downloadProfile(platform, profile) {
  try {
    // Fetch the full profile JSON
    const response = await fetch(`/api/smartir/platforms/${platform}/profiles/${profile.code}`)
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
    const response = await fetch(`/api/smartir/profiles/${profile.code}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform })
    })
    
    if (response.ok) {
      // Reload profiles first
      console.log('🔄 Reloading profiles for platform:', platform)
      await loadProfiles(platform)
      console.log('🔄 Updated profiles:', profiles.value[platform])
      
      // Wait for DOM update
      await nextTick()
      
      // Then refresh status
      await refreshStatus()
      console.log('🔄 Status refreshed')
      
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
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--ha-border-color);
  background: var(--ha-card-header-background, var(--ha-card-background));
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.header-left i {
  font-size: 24px;
  color: var(--primary-color);
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

/* Platforms Section */
.platforms-section {
  margin-bottom: 24px;
}

.platforms-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-text-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.platform-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.platform-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
  border-radius: 8px;
  border: 1px solid var(--ha-border-color);
}

.platform-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 8px;
}

.platform-icon i {
  font-size: 20px;
}

.platform-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.platform-name {
  font-weight: 600;
  color: var(--primary-text-color);
  font-size: 14px;
}

.device-count {
  font-size: 12px;
  color: var(--secondary-text-color);
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

/* Platform Cards */
.platform-card {
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.platform-card.expanded {
  grid-column: 1 / -1;
  max-width: 100%;
}

.platform-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.platform-header:hover {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
}

.platform-header .mdi-chevron-up,
.platform-header .mdi-chevron-down {
  margin-left: auto;
  color: var(--secondary-text-color);
  font-size: 20px;
}

/* Platform Profiles */
.platform-profiles {
  border-top: 1px solid var(--ha-border-color);
  padding: 12px;
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.02));
  animation: expandDown 0.3s ease-out;
  overflow: hidden;
}

@keyframes expandDown {
  from {
    opacity: 0;
    max-height: 0;
    padding-top: 0;
    padding-bottom: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
    padding-top: 12px;
    padding-bottom: 12px;
  }
}

.profiles-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  color: var(--secondary-text-color);
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid var(--ha-border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.profile-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.profile-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 6px;
  transition: all 0.2s;
}

.profile-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-name {
  font-weight: 600;
  color: var(--primary-text-color);
  font-size: 14px;
}

.profile-code {
  font-size: 12px;
  color: var(--secondary-text-color);
}

.profile-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  background: transparent;
  border: 1px solid var(--ha-border-color);
  color: var(--primary-text-color);
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--ha-primary-color);
  color: white;
  border-color: var(--ha-primary-color);
}

.action-btn.delete:hover {
  background: var(--error-color, #f44336);
  border-color: var(--error-color, #f44336);
}

.action-btn i {
  font-size: 16px;
}

.no-profiles {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: var(--secondary-text-color);
  text-align: center;
}

.no-profiles i {
  font-size: 32px;
  opacity: 0.5;
}

.no-profiles p {
  margin: 0;
  font-size: 14px;
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
