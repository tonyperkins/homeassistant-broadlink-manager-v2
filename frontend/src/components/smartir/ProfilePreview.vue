<template>
  <div class="profile-preview">
    <h3>Preview & Save</h3>
    
    <div class="preview-summary">
      <div class="summary-card">
        <i class="mdi mdi-check-circle"></i>
        <div>
          <h4>Profile Ready!</h4>
          <p>{{ profile.manufacturer }} {{ profile.model }}</p>
        </div>
      </div>
      
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-value">{{ commandCount }}</span>
          <span class="stat-label">Commands Learned</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ profile.platform }}</span>
          <span class="stat-label">Platform</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ profile.config.modes?.length || 0 }}</span>
          <span class="stat-label">HVAC Modes</span>
        </div>
      </div>
    </div>

    <div class="preview-tabs">
      <button 
        @click="activeTab = 'json'"
        class="tab-button"
        :class="{ active: activeTab === 'json' }"
      >
        <i class="mdi mdi-code-json"></i>
        SmartIR JSON
      </button>
      <button 
        @click="activeTab = 'yaml'"
        class="tab-button"
        :class="{ active: activeTab === 'yaml' }"
      >
        <i class="mdi mdi-file-code"></i>
        YAML Config
      </button>
      <button 
        @click="activeTab = 'instructions'"
        class="tab-button"
        :class="{ active: activeTab === 'instructions' }"
      >
        <i class="mdi mdi-information"></i>
        Instructions
      </button>
    </div>

    <div class="preview-content">
      <!-- JSON Tab -->
      <div v-if="activeTab === 'json'" class="tab-content">
        <div class="code-header">
          <h4>SmartIR Device Code JSON</h4>
          <button @click="copyJson" class="btn-copy">
            <i class="mdi mdi-content-copy"></i>
            {{ jsonCopied ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <pre class="code-block"><code>{{ formattedJson }}</code></pre>
        <p class="code-note">
          <i class="mdi mdi-information"></i>
          Save this as <code>10000.json</code> in your SmartIR codes directory
        </p>
      </div>

      <!-- YAML Tab -->
      <div v-if="activeTab === 'yaml'" class="tab-content">
        <div class="code-header">
          <h4>Home Assistant Configuration</h4>
          <button @click="copyYaml" class="btn-copy">
            <i class="mdi mdi-content-copy"></i>
            {{ yamlCopied ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <pre class="code-block"><code>{{ yamlConfig }}</code></pre>
        <p class="code-note">
          <i class="mdi mdi-information"></i>
          Add this to your <code>configuration.yaml</code> file
        </p>
      </div>

      <!-- Instructions Tab -->
      <div v-if="activeTab === 'instructions'" class="tab-content">
        <div class="instructions">
          <h4>Installation Steps</h4>
          
          <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-content">
              <h5>Get Next Code Number</h5>
              <p>Custom device codes start at 10000. Check your SmartIR codes directory to find the next available number.</p>
              <div class="code-path">
                <code>/config/custom_components/smartir/codes/{{ profile.platform }}/</code>
              </div>
            </div>
          </div>

          <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-content">
              <h5>Save JSON File</h5>
              <p>Copy the JSON from the "SmartIR JSON" tab and save it as <code>10000.json</code> (or your next available number) in the codes directory.</p>
            </div>
          </div>

          <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-content">
              <h5>Update Configuration</h5>
              <p>Copy the YAML from the "YAML Config" tab and add it to your <code>configuration.yaml</code> file. Update the <code>device_code</code> to match your JSON filename.</p>
            </div>
          </div>

          <div class="step-item">
            <div class="step-number">4</div>
            <div class="step-content">
              <h5>Restart Home Assistant</h5>
              <p>Restart Home Assistant to load the new configuration. Your climate entity will appear in the UI.</p>
            </div>
          </div>

          <div class="step-item">
            <div class="step-number">5</div>
            <div class="step-content">
              <h5>Test Your Device</h5>
              <p>Go to your climate entity and test different modes, temperatures, and fan speeds to ensure everything works correctly.</p>
            </div>
          </div>

          <div class="tips-section">
            <h4>
              <i class="mdi mdi-lightbulb"></i>
              Tips
            </h4>
            <ul>
              <li>Keep a backup of your JSON file in case you need to modify it</li>
              <li>Test all commands to ensure they work as expected</li>
              <li>You can share your profile with the SmartIR community on GitHub</li>
              <li>If a command doesn't work, you can re-learn it and update the JSON</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const props = defineProps({
  profile: {
    type: Object,
    required: true
  },
  jsonData: {
    type: Object,
    required: true
  },
  yamlConfig: {
    type: String,
    required: true
  }
})

const activeTab = ref('json')
const jsonCopied = ref(false)
const yamlCopied = ref(false)

const commandCount = computed(() => {
  return Object.keys(props.profile.commands || {}).length
})

const formattedJson = computed(() => {
  return JSON.stringify(props.jsonData, null, 2)
})

async function copyJson() {
  try {
    await navigator.clipboard.writeText(formattedJson.value)
    jsonCopied.value = true
    setTimeout(() => {
      jsonCopied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy JSON:', error)
    toast.error('Failed to copy to clipboard')
  }
}

async function copyYaml() {
  try {
    await navigator.clipboard.writeText(props.yamlConfig)
    yamlCopied.value = true
    setTimeout(() => {
      yamlCopied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy YAML:', error)
    toast.error('Failed to copy to clipboard')
  }
}
</script>

<style scoped>
.profile-preview h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.preview-summary {
  margin-bottom: 24px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
  border-radius: 8px;
  margin-bottom: 16px;
}

.summary-card i {
  font-size: 48px;
}

.summary-card h4 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.summary-card p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--secondary-text-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 2px solid var(--ha-border-color);
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--secondary-text-color);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: var(--primary-text-color);
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.03));
}

.tab-button.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.tab-button i {
  font-size: 18px;
}

.preview-content {
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  padding: 20px;
}

.tab-content {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.code-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.btn-copy {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-copy:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  margin: 0 0 12px 0;
  max-height: 400px;
  overflow-y: auto;
}

.code-block code {
  color: inherit;
}

.code-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 12px;
  background: rgba(33, 150, 243, 0.1);
  border-left: 4px solid #2196f3;
  border-radius: 4px;
  font-size: 13px;
  color: var(--primary-text-color);
}

.code-note i {
  color: #2196f3;
  font-size: 18px;
}

.code-note code {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.instructions h4 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.step-item {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.step-number {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 16px;
}

.step-content h5 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-text-color);
}

.step-content p {
  margin: 0 0 8px 0;
  color: var(--primary-text-color);
  font-size: 14px;
  line-height: 1.6;
}

.step-content code {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.code-path {
  margin-top: 8px;
  padding: 8px 12px;
  background: #1e1e1e;
  border-radius: 4px;
}

.code-path code {
  color: #4caf50;
  background: none;
  padding: 0;
}

.tips-section {
  margin-top: 32px;
  padding: 20px;
  background: rgba(255, 193, 7, 0.1);
  border-left: 4px solid #ffc107;
  border-radius: 4px;
}

.tips-section h4 {
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f57c00;
  font-size: 16px;
}

.tips-section i {
  font-size: 20px;
}

.tips-section ul {
  margin: 0;
  padding-left: 20px;
}

.tips-section li {
  margin-bottom: 8px;
  color: var(--primary-text-color);
  font-size: 14px;
  line-height: 1.6;
}

/* Dark mode adjustments */
:global(.dark-mode) .code-note {
  background: rgba(33, 150, 243, 0.15);
}

:global(.dark-mode) .tips-section {
  background: rgba(255, 193, 7, 0.15);
}

:global(.dark-mode) .step-content code {
  background: rgba(255, 255, 255, 0.1);
}

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .profile-preview h3 {
    font-size: 18px;
  }

  .preview-summary {
    padding: 14px;
  }

  .summary-card h4 {
    font-size: 16px;
  }

  .summary-card p {
    font-size: 13px;
  }

  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }

  .stat-value {
    font-size: 18px;
  }

  .stat-label {
    font-size: 11px;
  }

  .preview-tabs {
    gap: 6px;
    overflow-x: auto;
  }

  .tab-button {
    flex: 1;
    min-width: fit-content;
    padding: 8px 10px;
    font-size: 12px;
    white-space: nowrap;
  }

  .tab-button i {
    font-size: 16px;
  }

  .code-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .code-header h4 {
    font-size: 15px;
  }

  .btn-copy {
    width: 100%;
  }

  .code-block {
    font-size: 11px;
    padding: 12px;
    max-height: 300px;
  }

  .code-note {
    font-size: 12px;
    padding: 10px;
  }

  .step-item {
    gap: 12px;
  }

  .step-number {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }

  .step-content h5 {
    font-size: 14px;
  }

  .step-content p {
    font-size: 13px;
  }

  .code-path {
    padding: 6px 10px;
  }

  .code-path code {
    font-size: 11px;
    word-break: break-all;
  }

  .tips-section {
    padding: 14px;
  }

  .tips-section h4 {
    font-size: 14px;
  }

  .tips-section li {
    font-size: 13px;
  }
}
</style>
