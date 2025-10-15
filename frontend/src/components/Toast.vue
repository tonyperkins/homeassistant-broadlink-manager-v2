<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="[`toast-${toast.type}`]"
        >
          <i class="mdi" :class="getIcon(toast.type)"></i>
          <div class="toast-content">
            <div v-if="toast.title" class="toast-title">{{ toast.title }}</div>
            <div class="toast-message">{{ toast.message }}</div>
            <div v-if="toast.description" class="toast-description">{{ toast.description }}</div>
          </div>
          <button @click="removeToast(toast.id)" class="toast-close">
            <i class="mdi mdi-close"></i>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
let nextId = 0

function getIcon(type) {
  const icons = {
    success: 'mdi-check-circle',
    error: 'mdi-alert-circle',
    warning: 'mdi-alert',
    info: 'mdi-information'
  }
  return icons[type] || icons.info
}

function addToast({ message, title, description, type = 'info', duration = 5000 }) {
  const id = nextId++
  const toast = { id, message, title, description, type }
  
  toasts.value.push(toast)
  
  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }
  
  return id
}

function removeToast(id) {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

// Expose methods
defineExpose({
  addToast,
  removeToast,
  show: addToast,  // Alias for consistency
  success: (message, title) => addToast({ message, title, type: 'success' }),
  error: (message, title) => addToast({ message, title, type: 'error', duration: 8000 }),
  warning: (message, title) => addToast({ message, title, type: 'warning', duration: 6000 }),
  info: (message, title) => addToast({ message, title, type: 'info' })
})
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 400px;
}

.toast {
  background: var(--ha-card-background);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 300px;
  border-left: 4px solid;
}

.toast-success {
  border-left-color: var(--ha-success-color, #4caf50);
}

.toast-error {
  border-left-color: var(--ha-error-color, #f44336);
}

.toast-warning {
  border-left-color: var(--ha-warning-color, #ff9800);
}

.toast-info {
  border-left-color: var(--ha-info-color, #2196f3);
}

.toast i.mdi {
  font-size: 24px;
  flex-shrink: 0;
}

.toast-success i {
  color: var(--ha-success-color, #4caf50);
}

.toast-error i {
  color: var(--ha-error-color, #f44336);
}

.toast-warning i {
  color: var(--ha-warning-color, #ff9800);
}

.toast-info i {
  color: var(--ha-info-color, #2196f3);
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--ha-text-primary-color);
}

.toast-message {
  color: var(--ha-text-primary-color);
  font-size: 14px;
  line-height: 1.4;
  white-space: pre-line;
}

.toast-description {
  color: var(--ha-text-secondary-color);
  font-size: 13px;
  line-height: 1.4;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(var(--ha-border-rgb, 128, 128, 128), 0.2);
  white-space: pre-line;
}

.toast-close {
  background: transparent;
  border: none;
  color: var(--ha-text-secondary-color);
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toast-close:hover {
  background: rgba(0, 0, 0, 0.1);
}

/* Animations */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
