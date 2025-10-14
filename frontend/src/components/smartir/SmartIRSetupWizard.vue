<template>
  <div v-if="show" class="modal-overlay" @click.stop>
    <div class="setup-wizard" @click.stop>
      <div class="wizard-header">
        <h2>
          <i class="mdi mdi-cog"></i>
          SmartIR Configuration Setup
        </h2>
      </div>

      <div class="wizard-body">
        <!-- Warnings if configuration.yaml has platform entries -->
        <div v-if="warnings.length > 0" class="warning-section">
          <div class="warning-box">
            <i class="mdi mdi-alert"></i>
            <div>
              <h3>⚠️ Configuration Migration Needed</h3>
              <p>We detected existing platform entries in your configuration.yaml:</p>
              <ul>
                <li v-for="warning in warnings" :key="warning.platform">
                  <strong>{{ warning.platform }}:</strong> {{ warning.message }}
                </li>
              </ul>
              <p><strong>Action Required:</strong> Move these entries to <code>smartir/{{ platform }}.yaml</code> before continuing.</p>
            </div>
          </div>
        </div>

        <!-- Setup Instructions -->
        <div class="instructions">
          <h3>📝 One-Time Setup</h3>
          <p>To enable SmartIR device management, add this line to your <code>configuration.yaml</code>:</p>
          
          <div class="code-block">
            <code>{{ platform }}: !include smartir/{{ platform }}.yaml</code>
            <button @click="copyToClipboard" class="copy-btn" title="Copy to clipboard">
              <i class="mdi mdi-content-copy"></i>
            </button>
          </div>

          <div class="steps">
            <h4>Steps:</h4>
            <ol>
              <li v-if="warnings.length > 0">
                <strong>Move existing entries:</strong> Copy any existing <code>{{ platform }}:</code> entries from configuration.yaml to <code>smartir/{{ platform }}.yaml</code>
              </li>
              <li>
                <strong>Add include line:</strong> Add the line above to your configuration.yaml
              </li>
              <li>
                <strong>Save changes:</strong> Save configuration.yaml
              </li>
              <li>
                <strong>Continue here:</strong> Click "I've Completed Setup" below
              </li>
            </ol>
          </div>

          <div class="help-section">
            <button @click="showHelp = !showHelp" class="help-toggle">
              <i class="mdi" :class="showHelp ? 'mdi-chevron-up' : 'mdi-chevron-down'"></i>
              {{ showHelp ? 'Hide' : 'Show' }} Detailed Instructions
            </button>
            
            <div v-if="showHelp" class="help-content">
              <h4>Detailed Setup Guide:</h4>
              
              <div class="help-step">
                <h5>1. Open configuration.yaml</h5>
                <p>Location: <code>{{ configPath }}/configuration.yaml</code></p>
              </div>

              <div v-if="warnings.length > 0" class="help-step">
                <h5>2. Migrate Existing Entries (If Any)</h5>
                <p>If you have existing {{ platform }} entries, cut them from configuration.yaml and paste into:</p>
                <p><code>{{ configPath }}/smartir/{{ platform }}.yaml</code></p>
                <p class="note">Broadlink Manager will create this file automatically.</p>
              </div>

              <div class="help-step">
                <h5>{{ warnings.length > 0 ? '3' : '2' }}. Add Include Line</h5>
                <p>Add this to configuration.yaml:</p>
                <pre>{{ platform }}: !include smartir/{{ platform }}.yaml</pre>
              </div>

              <div class="help-step">
                <h5>{{ warnings.length > 0 ? '4' : '3' }}. Restart Home Assistant</h5>
                <p>After saving, you'll need to restart HA for changes to take effect.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Checkboxes -->
        <div class="checklist">
          <label class="checkbox-label">
            <input type="checkbox" v-model="setupCompleted" />
            <span>I've added the include line to configuration.yaml</span>
          </label>
          
          <label v-if="warnings.length > 0" class="checkbox-label">
            <input type="checkbox" v-model="migrationCompleted" />
            <span>I've migrated existing {{ platform }} entries (if any)</span>
          </label>
        </div>
      </div>

      <div class="wizard-footer">
        <button @click="$emit('close')" class="btn-secondary">
          Cancel
        </button>
        <button 
          @click="complete" 
          class="btn-primary"
          :disabled="!canContinue"
        >
          <i class="mdi mdi-check"></i>
          I've Completed Setup
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  platform: {
    type: String,
    required: true
  },
  warnings: {
    type: Array,
    default: () => []
  },
  configPath: {
    type: String,
    default: '/config'
  }
})

const emit = defineEmits(['close', 'complete'])

const toastRef = inject('toast')
const setupCompleted = ref(false)
const migrationCompleted = ref(false)
const showHelp = ref(false)

const canContinue = computed(() => {
  if (props.warnings.length > 0) {
    return setupCompleted.value && migrationCompleted.value
  }
  return setupCompleted.value
})

function copyToClipboard() {
  const text = `${props.platform}: !include smartir/${props.platform}.yaml`
  navigator.clipboard.writeText(text).then(() => {
    toastRef.value?.success('Include line copied to clipboard!', '✅ Copied')
  }).catch(err => {
    console.error('Failed to copy:', err)
    toastRef.value?.error('Failed to copy to clipboard', '❌ Copy Failed')
  })
}

function complete() {
  emit('complete')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.setup-wizard {
  background: var(--ha-card-background);
  border-radius: 12px;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.wizard-header {
  padding: 24px;
  border-bottom: 1px solid var(--ha-border-color);
}

.wizard-header h2 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--ha-text-primary-color);
  font-size: 24px;
}

.wizard-header i {
  color: var(--ha-primary-color);
  font-size: 28px;
}

.wizard-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.warning-section {
  margin-bottom: 24px;
}

.warning-box {
  background: rgba(255, 152, 0, 0.1);
  border-left: 4px solid var(--ha-warning-color);
  padding: 16px;
  border-radius: 4px;
  display: flex;
  gap: 12px;
}

.warning-box i {
  color: var(--ha-warning-color);
  font-size: 24px;
  flex-shrink: 0;
}

.warning-box h3 {
  margin: 0 0 8px 0;
  color: var(--ha-text-primary-color);
}

.warning-box p {
  margin: 8px 0;
  color: var(--ha-text-primary-color);
}

.warning-box ul {
  margin: 8px 0;
  padding-left: 20px;
}

.warning-box code {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
}

.instructions h3 {
  margin: 0 0 12px 0;
  color: var(--ha-text-primary-color);
}

.instructions p {
  margin: 8px 0;
  color: var(--ha-text-primary-color);
  line-height: 1.6;
}

.instructions code {
  background: rgba(var(--ha-primary-color-rgb, 3, 169, 244), 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  color: var(--ha-primary-color);
}

.code-block {
  background: var(--ha-surface-color);
  border: 1px solid var(--ha-border-color);
  border-radius: 6px;
  padding: 16px;
  margin: 16px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.code-block code {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: var(--ha-text-primary-color);
  background: none;
  padding: 0;
}

.copy-btn {
  background: var(--ha-primary-color);
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: opacity 0.2s;
}

.copy-btn:hover {
  opacity: 0.9;
}

.steps {
  margin: 20px 0;
}

.steps h4 {
  margin: 0 0 12px 0;
  color: var(--ha-text-primary-color);
}

.steps ol {
  margin: 0;
  padding-left: 24px;
  color: var(--ha-text-primary-color);
}

.steps li {
  margin-bottom: 12px;
  line-height: 1.6;
}

.steps strong {
  color: var(--ha-primary-color);
}

.help-section {
  margin-top: 24px;
  border-top: 1px solid var(--ha-border-color);
  padding-top: 16px;
}

.help-toggle {
  background: transparent;
  border: none;
  color: var(--ha-primary-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 0;
}

.help-toggle:hover {
  opacity: 0.8;
}

.help-content {
  margin-top: 16px;
}

.help-step {
  margin-bottom: 20px;
}

.help-step h5 {
  margin: 0 0 8px 0;
  color: var(--ha-text-primary-color);
  font-size: 16px;
}

.help-step p {
  margin: 4px 0;
  color: var(--ha-text-secondary-color);
}

.help-step pre {
  background: var(--ha-surface-color);
  border: 1px solid var(--ha-border-color);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.help-step .note {
  font-style: italic;
  color: var(--ha-text-secondary-color);
  font-size: 13px;
}

.checklist {
  margin-top: 24px;
  padding: 16px;
  background: rgba(var(--ha-success-rgb, 76, 175, 80), 0.05);
  border-radius: 6px;
  border: 1px solid rgba(var(--ha-success-rgb, 76, 175, 80), 0.2);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  color: var(--ha-text-primary-color);
  font-size: 15px;
}

.checkbox-label:last-child {
  margin-bottom: 0;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.wizard-footer {
  padding: 20px 24px;
  border-top: 1px solid var(--ha-border-color);
  display: flex;
  gap: 12px;
  justify-content: flex-end;
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

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
</style>
