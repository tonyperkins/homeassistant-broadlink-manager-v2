<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Learn Command: {{ device.friendly_name || device.name }}</h2>
        <button @click="$emit('cancel')" class="close-btn">
          <i class="mdi mdi-close"></i>
        </button>
      </div>

      <div class="modal-body">
        <!-- Learning Form -->
        <form v-if="state === 'ready'" @submit.prevent="startLearning">
          <!-- Command Name -->
          <div class="form-group">
            <label for="command-name">Command Name *</label>
            <input
              id="command-name"
              v-model="commandName"
              type="text"
              placeholder="e.g., power, volume_up"
              required
              autofocus
            />
            <small>Enter a descriptive name for this command</small>
          </div>

          <!-- Command Type -->
          <div class="form-group">
            <label>Command Type *</label>
            <div class="radio-group">
              <label class="radio-label">
                <input type="radio" v-model="commandType" value="ir" />
                <span>IR (Infrared)</span>
              </label>
              <label class="radio-label">
                <input type="radio" v-model="commandType" value="rf" />
                <span>RF (Radio Frequency)</span>
              </label>
            </div>
          </div>

          <!-- Learn Button -->
          <div class="form-actions">
            <button type="submit" class="btn btn-primary">
              <i class="mdi mdi-remote-tv"></i>
              Start Learning
            </button>
          </div>
        </form>

        <!-- Preparing State -->
        <div v-if="state === 'preparing'" class="learning-state">
          <div class="learning-icon">
            <i class="mdi mdi-cog mdi-spin"></i>
          </div>
          <h3>Preparing Device...</h3>
          <p class="instruction">Connecting and authenticating with Broadlink device</p>
          <p class="sub-instruction">Please wait, this takes a few seconds</p>
          <div class="progress-bar">
            <div class="progress-fill indeterminate"></div>
          </div>
        </div>

        <!-- IR Learning State -->
        <div v-if="state === 'learning-ir'" class="learning-state">
          <div class="learning-icon">
            <i class="mdi mdi-remote mdi-spin"></i>
          </div>
          <h3>Learning IR Command</h3>
          <p class="instruction">Point your remote at the Broadlink device and press the button</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <p class="timer">{{ elapsed }}s / 30s</p>
          <button @click="cancelLearning" class="btn btn-secondary">Cancel</button>
        </div>

        <!-- RF Learning State - Step 1 -->
        <div v-if="state === 'learning-rf-sweep'" class="learning-state">
          <div class="learning-icon">
            <i class="mdi mdi-radio-tower mdi-spin"></i>
          </div>
          <h3>RF Learning - Step 1 of 2</h3>
          <p class="instruction">Press and HOLD the button for 2-3 seconds</p>
          <p class="sub-instruction">Scanning for RF frequency...</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <p class="timer">{{ elapsed }}s / 30s</p>
          <button @click="cancelLearning" class="btn btn-secondary">Cancel</button>
        </div>

        <!-- RF Learning State - Step 2 -->
        <div v-if="state === 'learning-rf-capture'" class="learning-state">
          <div class="learning-icon success">
            <i class="mdi mdi-check-circle"></i>
          </div>
          <h3>RF Frequency Locked!</h3>
          <p class="frequency" v-if="rfFrequency">{{ rfFrequency }} MHz</p>
          <p class="instruction">Now press the button again (short press)</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <p class="timer">{{ elapsed }}s / 30s</p>
          <button @click="cancelLearning" class="btn btn-secondary">Cancel</button>
        </div>

        <!-- Success State -->
        <div v-if="state === 'success'" class="success-state">
          <div class="success-icon">
            <i class="mdi mdi-check-circle"></i>
          </div>
          <h3>Command Learned Successfully!</h3>
          <div class="command-details">
            <p><strong>Name:</strong> {{ commandName }}</p>
            <p><strong>Type:</strong> {{ commandType.toUpperCase() }}</p>
            <p v-if="rfFrequency"><strong>Frequency:</strong> {{ rfFrequency }} MHz</p>
            <p><strong>Data Length:</strong> {{ dataLength }} characters</p>
          </div>

          <div class="test-options">
            <h4>Test Command:</h4>
            <div class="test-buttons">
              <button @click="testDirect" class="btn btn-primary" :disabled="testing">
                <i class="mdi mdi-flash" :class="{ 'mdi-spin': testing === 'direct' }"></i>
                Test Direct
              </button>
              <button @click="testViaHA" class="btn btn-primary" :disabled="testing">
                <i class="mdi mdi-home-assistant" :class="{ 'mdi-spin': testing === 'ha' }"></i>
                Test via HA
              </button>
              <button @click="skipTest" class="btn btn-secondary" :disabled="testing">
                Skip Testing
              </button>
            </div>
            <small>Test to verify the command works correctly</small>
          </div>
        </div>

        <!-- Error State -->
        <div v-if="state === 'error'" class="error-state">
          <div class="error-icon">
            <i class="mdi mdi-alert-circle"></i>
          </div>
          <h3>Learning Failed</h3>
          <p class="error-message">{{ errorMessage }}</p>
          <div class="error-actions">
            <button @click="resetForm" class="btn btn-primary">Try Again</button>
            <button @click="$emit('cancel')" class="btn btn-secondary">Close</button>
          </div>
        </div>

        <!-- Testing State -->
        <div v-if="state === 'testing'" class="testing-state">
          <div class="testing-icon">
            <i class="mdi mdi-play-circle mdi-spin"></i>
          </div>
          <h3>Testing Command...</h3>
          <p>Sending command to device</p>
          <p class="sub-instruction">Did your device respond?</p>
        </div>

        <!-- Test Result -->
        <div v-if="state === 'test-result'" class="test-result-state">
          <div class="result-icon" :class="testSuccess ? 'success' : 'error'">
            <i :class="testSuccess ? 'mdi mdi-check-circle' : 'mdi mdi-alert-circle'"></i>
          </div>
          <h3>{{ testSuccess ? 'Test Successful!' : 'Test Failed' }}</h3>
          <p v-if="testSuccess">Command sent successfully via {{ testMethod }}</p>
          <p v-else class="error-message">{{ errorMessage }}</p>
          <div class="result-actions">
            <button v-if="testSuccess" @click="learnAnother" class="btn btn-primary">
              Learn Another Command
            </button>
            <button v-if="!testSuccess" @click="state = 'success'" class="btn btn-primary">
              Try Different Test
            </button>
            <button @click="finish" class="btn btn-secondary">
              {{ testSuccess ? 'Done' : 'Close' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import api from '@/services/api'

const props = defineProps({
  device: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['cancel', 'learned'])

// Form state
const commandName = ref('')
const commandType = ref('ir')

// Learning state
const state = ref('ready') // ready, learning-ir, learning-rf-sweep, learning-rf-capture, success, error, testing, test-result
const elapsed = ref(0)
const progressPercent = computed(() => (elapsed.value / 30) * 100)
const rfFrequency = ref(null)
const dataLength = ref(0)
const errorMessage = ref('')

// Testing state
const testing = ref(null) // null, 'direct', 'ha'
const testSuccess = ref(false)
const testMethod = ref('')

// Timer
let timer = null
let startTime = null

const startTimer = () => {
  startTime = Date.now()
  elapsed.value = 0
  timer = setInterval(() => {
    elapsed.value = Math.floor((Date.now() - startTime) / 1000)
  }, 100)
}

const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onUnmounted(() => {
  stopTimer()
})

const startLearning = async () => {
  if (!commandName.value.trim()) return

  try {
    // Get entity_id from device (could be broadlink_entity or controller_device for SmartIR)
    const entityId = props.device.broadlink_entity || props.device.controller_device
    
    if (!entityId) {
      errorMessage.value = 'No Broadlink entity configured for this device'
      state.value = 'error'
      return
    }
    
    // Show preparing state first
    state.value = 'preparing'
    
    // After 6 seconds, switch to learning state (device should be ready by then)
    const learningStateTimer = setTimeout(() => {
      if (commandType.value === 'ir') {
        state.value = 'learning-ir'
      } else {
        state.value = 'learning-rf-sweep'
      }
      startTimer()
    }, 6000)

    const response = await api.post('/api/commands/learn/direct', {
      device_id: props.device.id,
      entity_id: entityId,
      command_name: commandName.value.trim(),
      command_type: commandType.value
    })
    
    // Clear the timer if request completes early
    clearTimeout(learningStateTimer)

    stopTimer()

    if (response.data.success) {
      // Success!
      dataLength.value = response.data.data_length
      if (response.data.frequency) {
        rfFrequency.value = response.data.frequency
      }
      state.value = 'success'
    } else {
      errorMessage.value = response.data.error || 'Learning failed'
      state.value = 'error'
    }
  } catch (error) {
    stopTimer()
    errorMessage.value = error.response?.data?.error || error.message || 'Learning failed'
    state.value = 'error'
  }
}

const cancelLearning = () => {
  stopTimer()
  state.value = 'ready'
  elapsed.value = 0
}

const testDirect = async () => {
  testing.value = 'direct'
  state.value = 'testing'

  try {
    const entityId = props.device.broadlink_entity || props.device.controller_device
    const response = await api.post('/api/commands/test', {
      device_id: props.device.id,
      entity_id: entityId,
      command: commandName.value.trim(),
      device: props.device.device || props.device.id
    })

    testSuccess.value = response.data.success
    testMethod.value = 'direct connection'
    state.value = 'test-result'
  } catch (error) {
    testSuccess.value = false
    errorMessage.value = error.response?.data?.error || error.message
    state.value = 'test-result'
  } finally {
    testing.value = null
  }
}

const testViaHA = async () => {
  testing.value = 'ha'
  state.value = 'testing'

  try {
    const entityId = props.device.broadlink_entity || props.device.controller_device
    const response = await api.post('/api/commands/test', {
      device_id: props.device.id,
      entity_id: entityId,
      command: commandName.value.trim(),
      device: props.device.device || props.device.id
    })

    testSuccess.value = response.data.success
    testMethod.value = 'Home Assistant'
    state.value = 'test-result'
  } catch (error) {
    testSuccess.value = false
    errorMessage.value = error.response?.data?.error || error.message
    state.value = 'test-result'
  } finally {
    testing.value = null
  }
}

const skipTest = () => {
  finish()
}

const resetForm = () => {
  state.value = 'ready'
  elapsed.value = 0
  rfFrequency.value = null
  dataLength.value = 0
  errorMessage.value = ''
}

const learnAnother = () => {
  // Emit learned event
  emit('learned', {
    deviceId: props.device.id,
    commandName: commandName.value.trim(),
    commandType: commandType.value
  })

  // Reset for next command
  commandName.value = ''
  rfFrequency.value = null
  dataLength.value = 0
  state.value = 'ready'
}

const finish = () => {
  // Emit learned event
  emit('learned', {
    deviceId: props.device.id,
    commandName: commandName.value.trim(),
    commandType: commandType.value
  })

  // Close dialog
  emit('cancel')
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
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: var(--ha-card-background);
  border-radius: 12px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--ha-shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--ha-border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.close-btn {
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

.close-btn:hover {
  background: var(--ha-hover-color);
  color: var(--ha-text-primary-color);
}

.close-btn i {
  font-size: 24px;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

/* Form Styles */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
  font-size: 14px;
}

.form-group input[type="text"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--ha-border-color);
  border-radius: 6px;
  background: var(--ha-card-background);
  color: var(--ha-text-primary-color);
  font-size: 14px;
}

.form-group input[type="text"]:focus {
  outline: none;
  border-color: var(--ha-primary-color);
}

.form-group small {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--ha-text-secondary-color);
}

.radio-group {
  display: flex;
  gap: 20px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--ha-text-primary-color);
}

.radio-label input[type="radio"] {
  cursor: pointer;
}

.form-actions {
  margin-top: 24px;
}

/* Learning States */
.learning-state,
.success-state,
.error-state,
.testing-state,
.test-result-state {
  text-align: center;
  padding: 20px;
}

.learning-icon,
.success-icon,
.error-icon,
.testing-icon,
.result-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.learning-icon i {
  color: var(--ha-primary-color);
}

.success-icon i,
.result-icon.success i {
  color: var(--ha-success-color, #4caf50);
}

.error-icon i,
.result-icon.error i {
  color: var(--ha-error-color, #f44336);
}

.testing-icon i {
  color: var(--ha-primary-color);
}

.learning-state h3,
.success-state h3,
.error-state h3,
.testing-state h3,
.test-result-state h3 {
  margin: 0 0 12px 0;
  font-size: 20px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.instruction {
  font-size: 16px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
  margin: 12px 0;
}

.sub-instruction {
  font-size: 14px;
  color: var(--ha-text-secondary-color);
  margin: 8px 0;
}

.frequency {
  font-size: 18px;
  font-weight: 600;
  color: var(--ha-primary-color);
  margin: 8px 0;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--ha-border-color);
  border-radius: 4px;
  overflow: hidden;
  margin: 20px 0 12px 0;
}

.progress-fill {
  height: 100%;
  background: var(--ha-primary-color);
  transition: width 0.1s linear;
}

.progress-fill.indeterminate {
  width: 100% !important;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--ha-primary-color) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: indeterminate 1.5s ease-in-out infinite;
}

@keyframes indeterminate {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.timer {
  font-size: 14px;
  color: var(--ha-text-secondary-color);
  margin: 8px 0 20px 0;
}

/* Command Details */
.command-details {
  background: var(--ha-hover-color);
  border-radius: 8px;
  padding: 16px;
  margin: 20px 0;
  text-align: left;
}

.command-details p {
  margin: 8px 0;
  font-size: 14px;
  color: var(--ha-text-primary-color);
}

.command-details strong {
  font-weight: 600;
  margin-right: 8px;
}

/* Test Options */
.test-options {
  margin-top: 24px;
}

.test-options h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.test-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 8px;
}

.test-buttons .btn {
  flex: 1;
  max-width: 150px;
}

.test-options small {
  display: block;
  font-size: 12px;
  color: var(--ha-text-secondary-color);
}

/* Error Message */
.error-message {
  color: var(--ha-error-color, #f44336);
  font-size: 14px;
  margin: 12px 0;
}

/* Actions */
.error-actions,
.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}

/* Buttons */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--ha-primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-secondary {
  background: var(--ha-hover-color);
  color: var(--ha-text-primary-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--ha-border-color);
}

.btn i {
  font-size: 18px;
}

.btn-large {
  width: 100%;
  padding: 12px 24px;
  font-size: 16px;
}
</style>
