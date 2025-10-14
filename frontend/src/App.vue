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
          <button @click="toggleDarkMode" class="icon-button" title="Toggle Dark Mode">
            <i :class="darkMode ? 'mdi mdi-weather-night' : 'mdi mdi-weather-sunny'"></i>
          </button>
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
import { ref, provide, onMounted, getCurrentInstance } from 'vue'
import Dashboard from './views/Dashboard.vue'
import Toast from './components/Toast.vue'
import { smartirService } from './services/smartir'

const toastRef = ref(null)

const darkMode = ref(false)
const smartirStatus = ref(null)

const toggleDarkMode = () => {
  darkMode.value = !darkMode.value
  document.body.classList.toggle('dark-mode', darkMode.value)
  localStorage.setItem('darkMode', darkMode.value)
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

onMounted(async () => {
  // Load dark mode preference
  const savedDarkMode = localStorage.getItem('darkMode')
  if (savedDarkMode === 'true') {
    darkMode.value = true
    document.body.classList.add('dark-mode')
  }
  
  // Check SmartIR status
  await checkSmartIR()
  
  // Make toast available globally
  const app = getCurrentInstance()
  if (app && toastRef.value) {
    app.appContext.config.globalProperties.$toast = toastRef.value
  }
})

// Provide SmartIR status and toast to all child components
provide('smartirStatus', smartirStatus)
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
</style>
