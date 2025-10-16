<template>
  <div id="app" class="app-container">
    <header class="app-header">
      <div class="header-content">
        <div class="header-left">
          <i class="mdi mdi-remote"></i>
          <h1>Broadlink Manager v2</h1>
          <span class="beta-badge">BETA</span>
        </div>
        <div class="header-right">
          <button @click="cycleTheme" class="icon-button" :title="themeTooltip">
            <i :class="themeIcon"></i>
          </button>
          <div class="settings-menu-container">
            <button @click="showSettingsMenu = !showSettingsMenu" class="icon-button" title="Settings">
              <i class="mdi mdi-cog"></i>
            </button>
            <div v-if="showSettingsMenu" class="settings-menu">
              <div class="menu-section-title">Integration Settings</div>
              <div 
                class="menu-item toggle-item" 
                :class="{ disabled: !smartirInstalled }"
                @click="smartirInstalled ? toggleSmartIR() : null"
                :title="!smartirInstalled ? 'SmartIR is not installed' : ''"
              >
                <div class="toggle-content">
                  <i class="mdi mdi-air-conditioner"></i>
                  <span>SmartIR Integration</span>
                  <span v-if="!smartirInstalled" class="not-installed-label">(Not Installed)</span>
                </div>
                <div class="toggle-switch" :class="{ active: smartirEnabled && smartirInstalled, disabled: !smartirInstalled }">
                  <div class="toggle-slider"></div>
                </div>
              </div>
              <a v-if="smartirEnabled" href="https://github.com/smartHomeHub/SmartIR" target="_blank" class="menu-item menu-link menu-subitem">
                <i class="mdi mdi-github"></i>
                <span>SmartIR on GitHub</span>
              </a>
              <button v-if="smartirEnabled" @click="updateSmartIRIndex" class="menu-item menu-subitem" :disabled="updatingIndex">
                <i class="mdi" :class="updatingIndex ? 'mdi-loading mdi-spin' : 'mdi-refresh'"></i>
                <span>{{ updatingIndex ? 'Updating...' : 'Update Device Index' }}</span>
              </button>
              
              <div class="menu-divider"></div>
              <div class="menu-section-title">Diagnostics</div>
              <button @click="copyDiagnostics" class="menu-item" :disabled="loadingDiagnostics">
                <i class="mdi mdi-content-copy"></i>
                <span>Copy Diagnostics</span>
              </button>
              <button @click="downloadDiagnostics" class="menu-item" :disabled="loadingDiagnostics">
                <i class="mdi mdi-download"></i>
                <span>Download Diagnostics</span>
              </button>
              
              <div class="menu-divider"></div>
              <div class="menu-section-title">Help & Support</div>
              <a href="https://github.com/tonyperkins/homeassistant-broadlink-manager-v2#readme" target="_blank" class="menu-item menu-link">
                <i class="mdi mdi-book-open-variant"></i>
                <span>Documentation</span>
              </a>
              <a href="https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues" target="_blank" class="menu-item menu-link">
                <i class="mdi mdi-bug"></i>
                <span>Report Issue</span>
              </a>
              
              <div class="menu-divider"></div>
              <div class="menu-section-title">Community</div>
              <a href="https://community.home-assistant.io/t/broadlink-manager-modern-web-interface-for-broadlink-devices/938473" target="_blank" class="menu-item menu-link">
                <i class="mdi mdi-forum"></i>
                <span>HA Forum Discussion</span>
              </a>
              <a href="https://www.reddit.com/r/homeassistant/comments/1o1q3kf/release_broadlink_manager_addon_a_modern_web_ui/" target="_blank" class="menu-item menu-link">
                <i class="mdi mdi-reddit"></i>
                <span>Reddit Discussion</span>
              </a>
              
              <div class="menu-divider"></div>
              <div class="menu-section-title">Project</div>
              <a href="https://github.com/tonyperkins/homeassistant-broadlink-manager-v2" target="_blank" class="menu-item menu-link">
                <i class="mdi mdi-github"></i>
                <span>GitHub Repository</span>
              </a>
              <a href="https://ko-fi.com/tonyperkins" target="_blank" class="menu-item menu-link menu-item-sponsor">
                <i class="mdi mdi-coffee"></i>
                <span>Support on Ko-fi</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="app-main">
      <Dashboard />
    </main>

    <footer class="app-footer">
      <p>Broadlink Manager v2.0.0-beta.1 | Built with Vue 3</p>
    </footer>

    <!-- Toast Notifications -->
    <Toast ref="toastRef" />
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted, onUnmounted, getCurrentInstance } from 'vue'
import Dashboard from './views/Dashboard.vue'
import Toast from './components/Toast.vue'
import { smartirService } from './services/smartir'
import api from './services/api'

const toastRef = ref(null)

const theme = ref('light') // 'light', 'medium', 'dark'
const smartirStatus = ref(null)
const showSettingsMenu = ref(false)
const loadingDiagnostics = ref(false)
const updatingIndex = ref(false)
const smartirEnabled = ref(localStorage.getItem('smartir_enabled') !== 'false') // Default to true

// Check if SmartIR is actually installed
const smartirInstalled = computed(() => {
  return smartirStatus.value?.installed || false
})

const themeIcon = computed(() => {
  const icons = {
    light: 'mdi mdi-weather-sunny',
    medium: 'mdi mdi-weather-partly-cloudy',
    dark: 'mdi mdi-weather-night'
  }
  return icons[theme.value]
})

const themeTooltip = computed(() => {
  const tooltips = {
    light: 'Switch to Medium Theme',
    medium: 'Switch to Dark Theme',
    dark: 'Switch to Light Theme'
  }
  return tooltips[theme.value]
})

const cycleTheme = () => {
  const themes = ['light', 'medium', 'dark']
  const currentIndex = themes.indexOf(theme.value)
  const nextIndex = (currentIndex + 1) % themes.length
  theme.value = themes[nextIndex]
  
  // Remove all theme classes
  document.body.classList.remove('medium-mode', 'dark-mode')
  
  // Add the appropriate class
  if (theme.value === 'medium') {
    document.body.classList.add('medium-mode')
  } else if (theme.value === 'dark') {
    document.body.classList.add('dark-mode')
  }
  
  localStorage.setItem('theme', theme.value)
}

const checkSmartIR = async () => {
  try {
    const status = await smartirService.getStatus()
    smartirStatus.value = status
    
    // Log SmartIR status for debugging
    if (status.installed) {
      console.log('✅ SmartIR detected:', status.version)
    } else {
      console.log('ℹ️ SmartIR not detected')
    }
  } catch (error) {
    console.error('Error checking SmartIR:', error)
    smartirStatus.value = { installed: false, error: error.message }
  }
}

const copyDiagnostics = async () => {
  loadingDiagnostics.value = true
  try {
    const response = await api.get('/api/diagnostics/markdown')
    const markdown = response.data.markdown
    
    await navigator.clipboard.writeText(markdown)
    toastRef.value?.success('Diagnostic summary copied to clipboard!')
    showSettingsMenu.value = false
  } catch (error) {
    console.error('Error copying diagnostics:', error)
    toastRef.value?.error('Failed to copy diagnostics')
  } finally {
    loadingDiagnostics.value = false
  }
}

const downloadDiagnostics = async () => {
  loadingDiagnostics.value = true
  try {
    const response = await api.get('/api/diagnostics/download', {
      responseType: 'blob'
    })
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    // Extract filename from content-disposition header or use default
    const contentDisposition = response.headers['content-disposition']
    let filename = 'broadlink_manager_diagnostics.zip'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    toastRef.value?.success('Diagnostic bundle downloaded!')
    showSettingsMenu.value = false
  } catch (error) {
    console.error('Error downloading diagnostics:', error)
    toastRef.value?.error('Failed to download diagnostics')
  } finally {
    loadingDiagnostics.value = false
  }
}

// Close settings menu when clicking outside
const toggleSmartIR = () => {
  // Don't allow toggling if SmartIR is not installed
  if (!smartirInstalled.value) {
    return
  }
  
  smartirEnabled.value = !smartirEnabled.value
  localStorage.setItem('smartir_enabled', smartirEnabled.value.toString())
  
  // Refresh the page to apply changes
  window.location.reload()
}

const updateSmartIRIndex = async () => {
  updatingIndex.value = true
  try {
    const response = await api.post('/api/smartir/refresh-index')
    
    if (response.data.success) {
      toastRef.value?.success(
        `Updated to v${response.data.version} (${response.data.total_devices} devices)`,
        '✅ Index Updated'
      )
    } else {
      toastRef.value?.error(
        response.data.error || 'Unknown error',
        '❌ Update Failed'
      )
    }
  } catch (error) {
    console.error('Error updating SmartIR index:', error)
    toastRef.value?.error('Failed to update device index', '❌ Update Error')
  } finally {
    updatingIndex.value = false
    showSettingsMenu.value = false
  }
}

const handleClickOutside = (event) => {
  if (!event.target.closest('.settings-menu-container')) {
    showSettingsMenu.value = false
  }
}

onMounted(async () => {
  // Load theme preference
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme && ['light', 'medium', 'dark'].includes(savedTheme)) {
    theme.value = savedTheme
    if (savedTheme === 'medium') {
      document.body.classList.add('medium-mode')
    } else if (savedTheme === 'dark') {
      document.body.classList.add('dark-mode')
    }
  } else {
    // Migrate old darkMode setting
    const savedDarkMode = localStorage.getItem('darkMode')
    if (savedDarkMode === 'true') {
      theme.value = 'dark'
      document.body.classList.add('dark-mode')
      localStorage.setItem('theme', 'dark')
    }
  }
  
  // Check SmartIR status
  await checkSmartIR()
  
  // Make toast available globally
  const app = getCurrentInstance()
  if (app && toastRef.value) {
    app.appContext.config.globalProperties.$toast = toastRef.value
  }
  
  // Add click outside listener for settings menu
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Provide SmartIR status and toast to all child components
provide('smartirStatus', smartirStatus)
provide('smartirEnabled', smartirEnabled)
provide('refreshSmartIR', checkSmartIR)
provide('toast', toastRef)
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--ha-surface-color);
}

.app-header {
  background: var(--ha-card-background);
  border-bottom: 1px solid var(--ha-border-color);
  padding: 16px 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left i {
  font-size: 32px;
  color: var(--ha-primary-color);
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.beta-badge {
  background: var(--ha-warning-color);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.header-right {
  display: flex;
  gap: 8px;
}

.icon-button {
  background: transparent;
  border: none;
  color: var(--ha-text-primary-color);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.icon-button:hover {
  background: var(--ha-hover-color);
}

.icon-button i {
  font-size: 24px;
}

.app-main {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
}

.app-footer {
  background: var(--ha-card-background);
  border-top: 1px solid var(--ha-border-color);
  padding: 16px 24px;
  text-align: center;
  color: var(--ha-text-secondary-color);
  font-size: 14px;
}

.app-footer p {
  margin: 0;
}

/* Settings Menu */
.settings-menu-container {
  position: relative;
}

.settings-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 220px;
  z-index: 1000;
  overflow: hidden;
  animation: slideDown 0.2s ease-out;
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

.menu-item {
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: transparent;
  color: var(--ha-text-primary-color);
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  transition: background 0.2s;
  text-decoration: none;
}

.menu-item:hover:not(:disabled) {
  background: var(--ha-hover-color);
}

.menu-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-item i {
  font-size: 20px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.menu-item span {
  flex: 1;
}

.menu-link {
  color: var(--ha-text-primary-color);
}

.menu-divider {
  height: 1px;
  background: var(--ha-border-color);
  margin: 8px 0;
}

.menu-section-title {
  padding: 8px 16px 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--ha-text-secondary-color);
  opacity: 0.7;
}

.menu-item-sponsor {
  color: #ea4aaa;
  font-weight: 500;
}

.menu-item-sponsor:hover:not(:disabled) {
  background: rgba(234, 74, 170, 0.1);
}

.menu-item-sponsor i {
  color: #ea4aaa;
}

/* Toggle Item */
.toggle-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.toggle-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.not-installed-label {
  font-size: 11px;
  color: var(--ha-text-secondary-color);
  font-weight: normal;
  opacity: 0.8;
}

.toggle-switch {
  width: 44px;
  height: 24px;
  background: var(--ha-border-color);
  border-radius: 12px;
  position: relative;
  transition: background 0.3s;
  flex-shrink: 0;
}

.toggle-switch.active {
  background: var(--ha-primary-color);
}

.toggle-switch.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-slider {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-slider {
  transform: translateX(20px);
}

.menu-subitem {
  padding-left: 44px;
  font-size: 13px;
  opacity: 0.9;
}
</style>
