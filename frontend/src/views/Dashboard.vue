<template>
  <div class="dashboard">
    <!-- SmartIR Banner -->
    <SmartIRBanner />

    <!-- Welcome Banner -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="banner-icon">
          <i class="mdi mdi-rocket-launch"></i>
        </div>
        <div class="banner-text">
          <h2>Welcome to Broadlink Manager v2!</h2>
          <p>Manage your IR/RF devices with a modern Vue 3 interface</p>
        </div>
      </div>
      <div class="status-badges">
        <span class="badge success">
          <i class="mdi mdi-check-circle"></i>
          Vue 3 Ready
        </span>
        <span class="badge warning">
          <i class="mdi mdi-beta"></i>
          Beta
        </span>
      </div>
    </div>

    <!-- Device List Component -->
    <DeviceList />

    <!-- SmartIR Status Card -->
    <SmartIRStatusCard 
      @create-profile="handleCreateProfile"
      @edit-profile="handleEditProfile"
      @show-install-guide="handleShowInstallGuide"
    />

    <!-- Info Cards -->
    <div class="info-cards">
      <div class="info-card compact">
        <i class="mdi mdi-information"></i>
        <p>Beta version under development</p>
      </div>

      <div class="info-card compact">
        <i class="mdi mdi-github"></i>
        <p>
          <a href="https://github.com/tonyperkins/homeassistant-broadlink-manager-v2" target="_blank">
            View on GitHub
          </a>
        </p>
      </div>

      <div class="info-card compact">
        <i class="mdi mdi-bug"></i>
        <p>
          <a href="https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues" target="_blank">
            Report it on GitHub Issues
          </a>
        </p>
      </div>

      <div class="info-card compact">
        <i class="mdi mdi-reddit"></i>
        <p>
          <a href="https://www.reddit.com/r/homeassistant/comments/1o1q3kf/release_broadlink_manager_addon_a_modern_web_ui/" target="_blank">
            Join the discussion on Reddit
          </a>
        </p>
      </div>

      <div class="info-card compact">
        <i class="mdi mdi-forum"></i>
        <p>
          <a href="https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/discussions/1" target="_blank">
            Chat on GitHub Discussions
          </a>
        </p>
      </div>
    </div>

    <!-- SmartIR Profile Builder Modal -->
    <SmartIRProfileBuilder
      :show="showProfileBuilder"
      :editMode="editMode"
      :editData="editData"
      @close="handleCloseProfileBuilder"
      @save="handleProfileSave"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToast } from '@/composables/useToast'
import DeviceList from '@/components/devices/DeviceList.vue'
import SmartIRBanner from '@/components/common/SmartIRBanner.vue'
import SmartIRStatusCard from '@/components/smartir/SmartIRStatusCard.vue'
import SmartIRProfileBuilder from '@/components/smartir/SmartIRProfileBuilder.vue'

const toast = useToast()

const showProfileBuilder = ref(false)
const editMode = ref(false)
const editData = ref(null)

// Event handlers for SmartIR Status Card
function handleCreateProfile() {
  editMode.value = false
  editData.value = null
  showProfileBuilder.value = true
}

async function handleEditProfile({ platform, profile }) {
  try {
    // Fetch the full profile data
    const response = await fetch(`/api/smartir/platforms/${platform}/profiles/${profile.code}`)
    if (!response.ok) {
      throw new Error('Failed to load profile')
    }
    
    const data = await response.json()
    
    // Try to find controller_data from YAML config
    let controllerData = ''
    try {
      const configResponse = await fetch(`/api/smartir/config/get-device?platform=${platform}&code=${profile.code}`)
      if (configResponse.ok) {
        const configData = await configResponse.json()
        controllerData = configData.controller_data || ''
        console.log('✅ Found controller_data from YAML:', controllerData)
      } else {
        console.warn('⚠️ No YAML entry found for this profile (this is OK for profiles not yet added to config)')
      }
    } catch (err) {
      console.warn('⚠️ Could not fetch controller_data from config:', err)
    }
    
    // Set edit mode and data
    editMode.value = true
    editData.value = {
      platform,
      code: profile.code,
      profile: {
        ...data.profile,
        controller_data: controllerData // Add controller_data from YAML
      }
    }
    showProfileBuilder.value = true
  } catch (err) {
    console.error('Error loading profile for edit:', err)
    toast.error('Failed to load profile for editing')
  }
}

function handleCloseProfileBuilder() {
  showProfileBuilder.value = false
  editMode.value = false
  editData.value = null
}

function handleShowInstallGuide() {
  // TODO: Open install guide modal
  console.log('Show install guide clicked')
  // For now, open GitHub in new tab
  window.open('https://github.com/smartHomeHub/SmartIR', '_blank')
}

function handleProfileSave(result) {
  console.log('Profile saved:', result)
  // Close the builder
  handleCloseProfileBuilder()
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100vh;
  position: relative;
  padding-bottom: 200px; /* Space for fixed footer */
}

.welcome-banner {
  background: linear-gradient(135deg, var(--ha-primary-color), #0288d1);
  border-radius: 12px;
  padding: 24px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--ha-shadow-md);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.banner-icon i {
  font-size: 48px;
}

.banner-text h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 500;
}

.banner-text p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.status-badges {
  display: flex;
  gap: 8px;
}

.badge {
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.badge.success {
  background: rgba(76, 175, 80, 0.9);
  color: white;
}

.badge.warning {
  background: rgba(255, 152, 0, 0.9);
  color: white;
}

.badge i {
  font-size: 14px;
}

.info-cards {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  padding: 16px;
  background: var(--ha-surface-color);
  border-top: 1px solid var(--ha-border-color);
  z-index: 10;
}

.info-card {
  background: var(--ha-card-background);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--ha-border-color);
  display: flex;
  gap: 12px;
  align-items: center;
}

.info-card i {
  font-size: 24px;
  color: var(--ha-primary-color);
  flex-shrink: 0;
}

.info-card.compact i {
  font-size: 12px;
}

.info-card h3 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
}

.info-card p {
  margin: 0;
  color: var(--ha-text-secondary-color);
  font-size: 13px;
  line-height: 1.4;
}

.info-card a {
  color: var(--ha-primary-color);
  text-decoration: none;
}

.info-card a:hover {
  text-decoration: underline;
}
</style>
