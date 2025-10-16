<template>
  <div v-if="shouldShow" class="smartir-banner" :class="bannerClass">
    <div class="banner-content">
      <div class="banner-icon">
        <i :class="iconClass"></i>
      </div>
      <div class="banner-message">
        <strong>{{ title }}</strong>
        <p>{{ message }}</p>
      </div>
      <div class="banner-actions">
        <button v-if="!status?.installed" @click="showGuide" class="btn-primary">
          Learn More
        </button>
        <button @click="dismiss" class="btn-text">
          {{ status?.installed ? 'Got it' : 'Dismiss' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'

const smartirStatus = inject('smartirStatus')
const dismissed = ref(false)

const shouldShow = computed(() => {
  if (!smartirStatus.value) return false
  if (dismissed.value) return false
  
  // Check localStorage for permanent dismissal
  const permanentlyDismissed = localStorage.getItem('smartir_banner_dismissed')
  if (permanentlyDismissed === 'true') return false
  
  return true
})

const bannerClass = computed(() => {
  return smartirStatus.value?.installed ? 'banner-success' : 'banner-info'
})

const iconClass = computed(() => {
  return smartirStatus.value?.installed 
    ? 'mdi mdi-check-circle' 
    : 'mdi mdi-information'
})

const title = computed(() => {
  if (smartirStatus.value?.installed) {
    return `SmartIR Detected (v${smartirStatus.value.version})`
  }
  return 'Want Climate Device Support?'
})

const message = computed(() => {
  if (smartirStatus.value?.installed) {
    return 'You can now create climate device profiles with full temperature and HVAC mode control.'
  }
  return 'Install SmartIR to unlock AC/heater control with temperature settings, HVAC modes, and 120+ pre-configured device profiles.'
})

function showGuide() {
  window.open('https://github.com/smartHomeHub/SmartIR', '_blank')
}

function dismiss() {
  dismissed.value = true
  
  // For success banner (SmartIR installed), dismiss permanently
  if (smartirStatus.value?.installed) {
    localStorage.setItem('smartir_banner_dismissed', 'true')
  } else {
    // For info banner (not installed), dismiss for session only
    // User can choose to dismiss permanently by clicking multiple times
    const dismissCount = parseInt(localStorage.getItem('smartir_banner_dismiss_count') || '0')
    if (dismissCount >= 2) {
      // After 3 dismissals, make it permanent
      localStorage.setItem('smartir_banner_dismissed', 'true')
    } else {
      localStorage.setItem('smartir_banner_dismiss_count', String(dismissCount + 1))
    }
  }
}

onMounted(() => {
  // Reset dismiss count if SmartIR status changes
  const lastStatus = localStorage.getItem('smartir_last_status')
  const currentStatus = smartirStatus.value?.installed ? 'installed' : 'not_installed'
  
  if (lastStatus !== currentStatus) {
    localStorage.removeItem('smartir_banner_dismissed')
    localStorage.removeItem('smartir_banner_dismiss_count')
    localStorage.setItem('smartir_last_status', currentStatus)
  }
})
</script>

<style scoped>
.smartir-banner {
  border-radius: 8px;
  margin-bottom: 1.5rem;
  padding: 1rem;
  animation: slideDown 0.3s ease-out;
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

.banner-info {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.banner-success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.banner-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
}

.banner-icon i {
  display: block;
}

.banner-message {
  flex: 1;
}

.banner-message strong {
  display: block;
  font-size: 1.1rem;
  margin-bottom: 0.25rem;
}

.banner-message p {
  margin: 0;
  opacity: 0.95;
  line-height: 1.5;
}

.banner-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.btn-primary {
  background: white;
  color: #667eea;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-text {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.8);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.btn-text:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.btn-text:active {
  transform: translateY(0);
}

/* Responsive design */
@media (max-width: 768px) {
  .banner-content {
    flex-direction: column;
    text-align: center;
  }
  
  .banner-actions {
    width: 100%;
    justify-content: center;
  }
  
  .btn-primary,
  .btn-text {
    flex: 1;
  }
}
</style>
