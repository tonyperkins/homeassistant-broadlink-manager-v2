<template>
  <div v-if="hasUntrackedDevices" class="discovery-banner">
    <div class="banner-content">
      <div class="banner-icon">
        <i class="mdi mdi-radar"></i>
      </div>
      <div class="banner-text">
        <h3>Untracked Devices Found</h3>
        <p>{{ untrackedDevices.length }} device{{ untrackedDevices.length > 1 ? 's' : '' }} with learned commands found in Broadlink storage</p>
      </div>
      <button @click="showDiscovery = true" class="btn btn-primary">
        <i class="mdi mdi-eye"></i>
        View Devices
      </button>
    </div>

    <!-- Discovery Modal -->
    <div v-if="showDiscovery" class="modal-overlay" @click.self="showDiscovery = false">
      <div class="modal-dialog">
        <div class="modal-header">
          <h2>Discovered Devices</h2>
          <button @click="showDiscovery = false" class="close-btn">
            <i class="mdi mdi-close"></i>
          </button>
        </div>

        <div class="modal-body">
          <p class="info-text">
            These devices have learned commands in Broadlink storage but are not being tracked. 
            Adopt them to manage their commands and generate Home Assistant entities.
          </p>

          <div class="device-list">
            <div v-for="device in untrackedDevices" :key="device.device_name" class="discovered-device">
              <div class="device-info">
                <div class="device-icon">
                  <i class="mdi mdi-devices"></i>
                </div>
                <div class="device-details">
                  <h4>{{ device.device_name }}</h4>
                  <span class="command-count">
                    <i class="mdi mdi-remote"></i>
                    {{ device.command_count }} command{{ device.command_count > 1 ? 's' : '' }}
                  </span>
                </div>
              </div>
              <div class="device-actions">
                <button @click="adoptDevice(device)" class="btn btn-primary">
                  <i class="mdi mdi-plus"></i>
                  Adopt
                </button>
                <button @click="confirmDeleteDevice(device)" class="btn btn-danger" title="Delete all commands">
                  <i class="mdi mdi-delete"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="showDiscovery = false" class="btn btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal-dialog modal-dialog-small">
        <div class="modal-header">
          <h2>Delete Untracked Device</h2>
          <button @click="showDeleteConfirm = false" class="close-btn">
            <i class="mdi mdi-close"></i>
          </button>
        </div>

        <div class="modal-body">
          <div class="warning-message">
            <i class="mdi mdi-alert"></i>
            <div>
              <p><strong>Are you sure you want to delete "{{ deviceToDelete?.device_name }}"?</strong></p>
              <p>This will permanently delete all {{ deviceToDelete?.command_count }} command{{ deviceToDelete?.command_count > 1 ? 's' : '' }} from Broadlink storage.</p>
              <p class="warning-text">This action cannot be undone.</p>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="showDeleteConfirm = false" class="btn btn-secondary" :disabled="deleting">
            Cancel
          </button>
          <button @click="deleteDevice" class="btn btn-danger" :disabled="deleting">
            <i class="mdi" :class="deleting ? 'mdi-loading mdi-spin' : 'mdi-delete'"></i>
            {{ deleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'

const toast = useToast()

const emit = defineEmits(['adopt'])

const untrackedDevices = ref([])
const showDiscovery = ref(false)
const showDeleteConfirm = ref(false)
const deviceToDelete = ref(null)
const deleting = ref(false)

const hasUntrackedDevices = computed(() => untrackedDevices.value.length > 0)

onMounted(async () => {
  await loadUntrackedDevices()
})

const loadUntrackedDevices = async () => {
  try {
    const response = await api.get('/api/devices/discover')
    untrackedDevices.value = response.data.untracked_devices || []
  } catch (error) {
    console.error('Error loading untracked devices:', error)
    untrackedDevices.value = []
  }
}

const adoptDevice = (device) => {
  showDiscovery.value = false
  emit('adopt', device)
}

const confirmDeleteDevice = (device) => {
  deviceToDelete.value = device
  showDeleteConfirm.value = true
}

const deleteDevice = async () => {
  if (!deviceToDelete.value) return
  
  const deviceName = deviceToDelete.value.device_name
  deleting.value = true
  
  try {
    const response = await api.delete(`/api/devices/untracked/${encodeURIComponent(deviceName)}`)
    
    if (response.data.success) {
      // Optimistically remove from list immediately (don't wait for storage)
      untrackedDevices.value = untrackedDevices.value.filter(
        d => d.device_name !== deviceName
      )
      
      // Close delete confirmation modal
      showDeleteConfirm.value = false
      deviceToDelete.value = null
      
      // If no more devices, close the discovery modal too
      if (untrackedDevices.value.length === 0) {
        showDiscovery.value = false
      }
      
      // Show success message
      toast.success(`Deleted all commands for '${deviceName}'`)
    } else {
      throw new Error(response.data.error || 'Failed to delete device')
    }
  } catch (error) {
    console.error('Error deleting device:', error)
    toast.error(`Failed to delete device: ${error.message}`)
  } finally {
    deleting.value = false
  }
}

// Expose method to refresh from parent
defineExpose({
  refresh: loadUntrackedDevices
})
</script>

<style scoped>
.discovery-banner {
  background: linear-gradient(135deg, rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1), rgba(var(--ha-primary-rgb, 3, 169, 244), 0.05));
  border: 2px solid var(--ha-primary-color, #03a9f4);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.banner-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--ha-primary-color, #03a9f4);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.banner-icon i {
  font-size: 28px;
  color: white;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.banner-text {
  flex: 1;
}

.banner-text h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.banner-text p {
  margin: 0;
  color: var(--ha-text-secondary-color);
  font-size: 14px;
}

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
}

.modal-dialog {
  background: var(--ha-card-background, #1c1c1c);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--ha-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--ha-text-primary-color);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--ha-text-secondary-color);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
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

.info-text {
  margin: 0 0 20px 0;
  padding: 12px;
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1);
  border-left: 3px solid var(--ha-primary-color, #03a9f4);
  border-radius: 4px;
  color: var(--ha-text-secondary-color);
  font-size: 14px;
  line-height: 1.5;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.discovered-device {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  transition: all 0.2s;
}

.discovered-device:hover {
  border-color: var(--ha-primary-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.device-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(var(--ha-primary-rgb, 3, 169, 244), 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.device-icon i {
  font-size: 24px;
  color: var(--ha-primary-color);
}

.device-details h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
}

.command-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--ha-text-secondary-color);
}

.command-count i {
  font-size: 14px;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--ha-border-color);
  display: flex;
  justify-content: flex-end;
  background: var(--ha-card-background);
  flex-shrink: 0;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
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
  background: var(--ha-hover-color);
}

.btn i {
  font-size: 18px;
}

.btn-danger {
  background: var(--ha-error-color, #f44336);
  color: white;
  padding: 10px 12px;
}

.btn-danger:hover:not(:disabled) {
  background: #d32f2f;
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-dialog-small {
  max-width: 500px;
}

.warning-message {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(var(--ha-error-rgb, 244, 67, 54), 0.1);
  border-left: 3px solid var(--ha-error-color, #f44336);
  border-radius: 4px;
}

.warning-message i {
  font-size: 24px;
  color: var(--ha-error-color, #f44336);
  flex-shrink: 0;
}

.warning-message p {
  margin: 0 0 8px 0;
  color: var(--ha-text-primary-color);
  font-size: 14px;
  line-height: 1.5;
}

.warning-message p:last-child {
  margin-bottom: 0;
}

.warning-text {
  color: var(--ha-error-color, #f44336);
  font-weight: 500;
}

/* Mobile Responsive Styles */
@media (max-width: 767px) {
  .discovery-banner {
    padding: 16px;
    margin-bottom: 16px;
  }

  .banner-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .banner-icon {
    width: 40px;
    height: 40px;
  }

  .banner-icon i {
    font-size: 24px;
  }

  .banner-text h3 {
    font-size: 16px;
  }

  .banner-text p {
    font-size: 13px;
  }

  .banner-content .btn {
    width: 100%;
    justify-content: center;
  }

  .modal-dialog {
    width: 95%;
    max-height: 90vh;
    margin: 16px;
  }

  .modal-header h2 {
    font-size: 18px;
  }

  .modal-body {
    padding: 16px;
  }

  .info-text {
    font-size: 13px;
  }

  .discovered-device {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
  }

  .device-info {
    width: 100%;
  }

  .device-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .device-actions .btn {
    flex: 1;
  }

  .device-actions .btn-danger {
    flex: 0 0 auto;
    min-width: 48px;
  }

  .modal-footer {
    padding: 12px 16px;
    flex-direction: column-reverse;
    gap: 8px;
  }

  .modal-footer .btn {
    width: 100%;
  }
}
</style>
