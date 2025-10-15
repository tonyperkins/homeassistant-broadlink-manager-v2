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
            <details v-if="details" class="error-details">
              <summary>Technical Details</summary>
              <pre>{{ details }}</pre>
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
import { ref, watch } from 'vue'

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
  }
})

const emit = defineEmits(['close'])

const handleClose = () => {
  emit('close')
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
