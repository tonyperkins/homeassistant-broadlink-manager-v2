<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click.self="handleClose">
        <div class="modal-container error-dialog">
          <div class="modal-header">
            <div class="header-icon error-icon">
              <i class="mdi mdi-alert-circle"></i>
            </div>
            <h3>{{ title }}</h3>
            <button @click="handleClose" class="close-button">
              <i class="mdi mdi-close"></i>
            </button>
          </div>
          
          <div class="modal-body">
            <p class="error-message">{{ message }}</p>
            <p v-if="suggestion" class="error-suggestion">
              <i class="mdi mdi-lightbulb-on"></i>
              {{ suggestion }}
            </p>
            
            <!-- Debug Information Section -->
            <details class="debug-section" :open="debugExpanded">
              <summary @click="debugExpanded = !debugExpanded">
                <i class="mdi" :class="debugExpanded ? 'mdi-chevron-down' : 'mdi-chevron-right'"></i>
                Debug Information
              </summary>
              <div class="debug-content">
                <div class="debug-actions">
                  <button @click="copyDebugInfo" class="btn-debug btn-copy">
                    <i class="mdi mdi-content-copy"></i>
                    Copy to Clipboard
                  </button>
                  <button @click="downloadDebugInfo" class="btn-debug btn-download">
                    <i class="mdi mdi-download"></i>
                    Download Report
                  </button>
                </div>
                
                <div class="debug-info">
                  <div class="debug-section-title">Error Details</div>
                  <pre>{{ debugInfo.error }}</pre>
                  
                  <div class="debug-section-title">Request Information</div>
                  <pre>{{ debugInfo.request }}</pre>
                  
                  <div class="debug-section-title">Response Information</div>
                  <pre>{{ debugInfo.response }}</pre>
                  
                  <div class="debug-section-title">Browser Information</div>
                  <pre>{{ debugInfo.browser }}</pre>
                  
                  <div class="debug-section-title">Application State</div>
                  <pre>{{ debugInfo.appState }}</pre>
                  
                  <div v-if="debugInfo.stackTrace" class="debug-section-title">Stack Trace</div>
                  <pre v-if="debugInfo.stackTrace">{{ debugInfo.stackTrace }}</pre>
                </div>
              </div>
            </details>
          </div>
          
          <div class="modal-footer">
            <button @click="handleClose" class="btn btn-primary">
              OK
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, computed, inject } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Error'
  },
  message: {
    type: String,
    required: true
  },
  suggestion: {
    type: String,
    default: ''
  },
  details: {
    type: String,
    default: ''
  },
  error: {
    type: Object,
    default: null
  },
  context: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])
const toast = inject('toast')

const debugExpanded = ref(false)

const handleClose = () => {
  emit('close')
}

// Collect comprehensive debug information
const debugInfo = computed(() => {
  const timestamp = new Date().toISOString()
  const error = props.error || {}
  
  return {
    error: JSON.stringify({
      message: props.message,
      title: props.title,
      details: props.details,
      errorObject: error.message || error.toString(),
      timestamp
    }, null, 2),
    
    request: JSON.stringify({
      method: error.config?.method?.toUpperCase() || 'N/A',
      url: error.config?.url || 'N/A',
      baseURL: error.config?.baseURL || 'N/A',
      headers: error.config?.headers || {},
      data: error.config?.data ? JSON.parse(error.config.data) : 'N/A',
      params: error.config?.params || {}
    }, null, 2),
    
    response: JSON.stringify({
      status: error.response?.status || 'N/A',
      statusText: error.response?.statusText || 'N/A',
      data: error.response?.data || 'N/A',
      headers: error.response?.headers || {}
    }, null, 2),
    
    browser: JSON.stringify({
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      screenResolution: `${window.screen.width}x${window.screen.height}`,
      colorDepth: window.screen.colorDepth,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      timestamp
    }, null, 2),
    
    appState: JSON.stringify({
      currentRoute: window.location.pathname,
      currentURL: window.location.href,
      referrer: document.referrer || 'N/A',
      context: props.context || {},
      localStorage: {
        smartir_simulate: localStorage.getItem('smartir_simulate_not_installed'),
        theme: localStorage.getItem('theme')
      }
    }, null, 2),
    
    stackTrace: error.stack || null
  }
})

const copyDebugInfo = async () => {
  const debugText = generateDebugReport()
  try {
    await navigator.clipboard.writeText(debugText)
    toast?.success('Debug information copied to clipboard', '✅ Copied')
  } catch (err) {
    console.error('Failed to copy:', err)
    toast?.error('Failed to copy to clipboard', '❌ Copy Failed')
  }
}

const downloadDebugInfo = () => {
  const debugText = generateDebugReport()
  const blob = new Blob([debugText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
  link.download = `broadlink-manager-error-${timestamp}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  toast?.success('Debug report downloaded', '✅ Downloaded')
}

const generateDebugReport = () => {
  return `Broadlink Manager - Error Report
${'='.repeat(60)}

Generated: ${new Date().toISOString()}
Title: ${props.title}
Message: ${props.message}
${props.suggestion ? `Suggestion: ${props.suggestion}\n` : ''}
${'='.repeat(60)}

ERROR DETAILS
${'-'.repeat(60)}
${debugInfo.value.error}

REQUEST INFORMATION
${'-'.repeat(60)}
${debugInfo.value.request}

RESPONSE INFORMATION
${'-'.repeat(60)}
${debugInfo.value.response}

BROWSER INFORMATION
${'-'.repeat(60)}
${debugInfo.value.browser}

APPLICATION STATE
${'-'.repeat(60)}
${debugInfo.value.appState}

${debugInfo.value.stackTrace ? `STACK TRACE\n${'-'.repeat(60)}\n${debugInfo.value.stackTrace}\n\n` : ''}
${'='.repeat(60)}
End of Report
`
}

// Close on Escape key
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        handleClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;  /* Higher than DeviceForm modal (10000) */
  padding: 20px;
}

.modal-container {
  background: var(--ha-card-background);
  border-radius: 12px;
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.error-dialog .modal-header {
  background: linear-gradient(135deg, #ef5350 0%, #e53935 100%);
  border-bottom: none;
  border-radius: 12px 12px 0 0;
}

.modal-header {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--ha-border-color);
}

.header-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.error-icon {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.header-icon i {
  font-size: 24px;
}

.error-dialog .modal-header h3 {
  flex: 1;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: white;
}

.modal-header h3 {
  flex: 1;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
}

.error-dialog .close-button {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.error-dialog .close-button:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.close-button {
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

.close-button:hover {
  background: var(--ha-hover-color);
  color: var(--ha-text-primary-color);
}

.close-button i {
  font-size: 20px;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.error-message {
  margin: 0 0 16px 0;
  color: var(--ha-text-primary-color);
  font-size: 15px;
  line-height: 1.6;
}

.error-suggestion {
  margin: 0 0 16px 0;
  padding: 12px 16px;
  background: rgba(33, 150, 243, 0.08);
  border-left: 3px solid rgba(33, 150, 243, 0.6);
  border-radius: 6px;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.error-suggestion i {
  color: rgba(33, 150, 243, 0.9);
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}

.error-details {
  margin-top: 16px;
  padding: 12px;
  background: var(--ha-surface-color);
  border: 1px solid var(--ha-border-color);
  border-radius: 6px;
}

.error-details summary {
  cursor: pointer;
  font-weight: 500;
  color: var(--ha-text-secondary-color);
  font-size: 13px;
  user-select: none;
}

.error-details summary:hover {
  color: var(--ha-text-primary-color);
}

.error-details pre {
  margin: 12px 0 0 0;
  padding: 12px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 4px;
  font-size: 12px;
  color: var(--ha-text-secondary-color);
  overflow-x: auto;
  font-family: 'Courier New', monospace;
}

/* Debug Section Styles */
.debug-section {
  margin-top: 20px;
  padding: 0;
  background: var(--ha-surface-color);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.debug-section summary {
  cursor: pointer;
  padding: 14px 16px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--ha-card-background);
  transition: background 0.2s;
}

.debug-section summary:hover {
  background: var(--ha-hover-color);
}

.debug-section summary i {
  font-size: 18px;
  transition: transform 0.2s;
}

.debug-content {
  padding: 16px;
  border-top: 1px solid var(--ha-border-color);
}

.debug-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.btn-debug {
  flex: 1;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--ha-border-color);
  background: var(--ha-card-background);
  color: var(--ha-text-primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-debug:hover {
  background: var(--ha-hover-color);
  border-color: var(--ha-primary-color);
}

.btn-debug i {
  font-size: 16px;
}

.btn-copy {
  border-color: rgba(33, 150, 243, 0.3);
}

.btn-copy:hover {
  background: rgba(33, 150, 243, 0.1);
  border-color: rgba(33, 150, 243, 0.6);
  color: rgba(33, 150, 243, 0.9);
}

.btn-download {
  border-color: rgba(76, 175, 80, 0.3);
}

.btn-download:hover {
  background: rgba(76, 175, 80, 0.1);
  border-color: rgba(76, 175, 80, 0.6);
  color: rgba(76, 175, 80, 0.9);
}

.debug-info {
  max-height: 400px;
  overflow-y: auto;
}

.debug-section-title {
  font-weight: 600;
  font-size: 12px;
  color: var(--ha-text-secondary-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 16px 0 8px 0;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--ha-border-color);
}

.debug-section-title:first-child {
  margin-top: 0;
}

.debug-info pre {
  margin: 0;
  padding: 12px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 4px;
  font-size: 11px;
  color: var(--ha-text-secondary-color);
  overflow-x: auto;
  font-family: 'Courier New', Consolas, Monaco, monospace;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--ha-border-color);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
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
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.8) translateY(-20px);
  opacity: 0;
}

/* Shake animation for error dialog */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.error-dialog .modal-container {
  animation: shake 0.5s ease-in-out;
}
</style>
