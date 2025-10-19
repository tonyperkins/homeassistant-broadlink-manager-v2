<template>
  <div v-if="isOpen" class="modal-overlay" @click.self.stop="cancel">
    <div class="modal-dialog confirm-dialog" @click.stop>
      <div class="modal-header">
        <h2>{{ title }}</h2>
      </div>
      
      <div class="modal-body">
        <p class="message-text">{{ message }}</p>
        
        <!-- Optional checkbox for additional action -->
        <div v-if="checkboxLabel" class="checkbox-option">
          <label>
            <input type="checkbox" v-model="checkboxValue" />
            <span>{{ checkboxLabel }}</span>
          </label>
        </div>
      </div>
      
      <div class="modal-footer">
        <button v-if="showCancel" @click.stop="cancel" class="btn btn-secondary">
          {{ cancelText }}
        </button>
        <button 
          v-if="confirmText" 
          @click.stop="confirm" 
          class="btn" 
          :class="dangerMode ? 'btn-danger' : 'btn-primary'"
          :disabled="confirmDisabled"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
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
    default: 'Confirm'
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: 'OK'
  },
  cancelText: {
    type: String,
    default: 'Cancel'
  },
  showCancel: {
    type: Boolean,
    default: true
  },
  dangerMode: {
    type: Boolean,
    default: false
  },
  confirmDisabled: {
    type: Boolean,
    default: false
  },
  checkboxLabel: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['confirm', 'cancel'])

const checkboxValue = ref(false)

// Reset checkbox when dialog opens
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    checkboxValue.value = false
  }
})

const confirm = () => {
  emit('confirm', checkboxValue.value)
}

const cancel = () => {
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
  z-index: 10001;
}

.confirm-dialog {
  max-width: 600px;
  width: 90%;
}

.modal-dialog {
  background: var(--ha-card-background, #1c1c1c);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--ha-border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--ha-text-primary-color);
}

.modal-body {
  padding: 24px;
}

.modal-body p {
  margin: 0 0 16px 0;
  color: var(--ha-text-primary-color);
  line-height: 1.5;
}

.message-text {
  white-space: pre-line;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 14px;
}

.checkbox-option {
  margin-top: 16px;
  padding: 12px;
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1);
  border-radius: 8px;
  border-left: 3px solid var(--ha-primary-color, #03a9f4);
}

.checkbox-option label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  color: var(--ha-text-primary-color);
}

.checkbox-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--ha-primary-color, #03a9f4);
}

.checkbox-option span {
  flex: 1;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--ha-border-color);
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--ha-primary-color, #03a9f4);
  color: white;
}

.btn-primary:hover {
  background: var(--ha-primary-color-dark, #0288d1);
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--ha-border-color);
  color: var(--ha-text-primary-color);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.05);
}

.btn-danger {
  background: var(--ha-error-color, #f44336);
  color: white;
}

.btn-danger:hover {
  background: var(--ha-error-color-dark, #d32f2f);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn:disabled:hover {
  background: var(--ha-error-color, #f44336);
}
</style>
