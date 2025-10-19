<template>
  <div class="dashboard">
    <!-- SmartIR Banner -->
    <SmartIRBanner v-if="smartirEnabled" />

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
      v-if="smartirEnabled"
      ref="smartirStatusCard"
      @create-profile="handleCreateProfile"
      @edit-profile="handleEditProfile"
    />

    <!-- SmartIR Profile Builder Modal -->
    <SmartIRProfileBuilder
      :show="showProfileBuilder"
      :editMode="editMode"
      :editData="editData"
      :startStep="profileStartStep"
      @close="handleCloseProfileBuilder"
      @save="handleProfileSave"
    />
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useToast } from '@/composables/useToast'
import DeviceList from '@/components/devices/DeviceList.vue'
import SmartIRBanner from '@/components/common/SmartIRBanner.vue'
import SmartIRStatusCard from '@/components/smartir/SmartIRStatusCard.vue'
import SmartIRProfileBuilder from '@/components/smartir/SmartIRProfileBuilder.vue'

const toast = useToast()
const smartirEnabled = inject('smartirEnabled')

const showProfileBuilder = ref(false)
const editMode = ref(false)
const editData = ref(null)
const profileStartStep = ref(0)
const smartirStatusCard = ref(null)

// Event handlers for SmartIR Status Card
function handleCreateProfile() {
  editMode.value = false
  editData.value = null
  profileStartStep.value = 0
  showProfileBuilder.value = true
}

async function handleEditProfile({ platform, profile, startStep }) {
  // Set desired start step early so the modal can jump to it on open
  profileStartStep.value = Number.isInteger(startStep) ? startStep : 0
  try {
    // Fetch the full profile data
    const response = await fetch(`api/smartir/platforms/${platform}/profiles/${profile.code}`)
    if (!response.ok) {
      throw new Error('Failed to load profile')
    }
    
    const data = await response.json()
    
    // Try to find controller_data from YAML config
    let controllerData = ''
    try {
      const configResponse = await fetch(`api/smartir/config/get-device?platform=${platform}&code=${profile.code}`)
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


async function handleProfileSave(result) {
  console.log('Profile saved:', result)
  // Close the builder
  handleCloseProfileBuilder()
  
  // Refresh the profiles list to show updated data
  if (smartirStatusCard.value && smartirStatusCard.value.loadAllProfiles) {
    await smartirStatusCard.value.loadAllProfiles()
    console.log('✅ Profiles list refreshed')
  }
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100vh;
  position: relative;
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
</style>
