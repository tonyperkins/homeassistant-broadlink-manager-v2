<template>
  <div class="device-list-view">
    <table class="device-table">
      <thead>
        <tr>
          <th>Device</th>
          <th>Room/Area</th>
          <th>Type</th>
          <th>Commands</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="device in devices" :key="device.entity_id" class="device-row">
          <!-- Device Info -->
          <td class="device-info">
            <div class="device-name">{{ device.friendly_name || device.name }}</div>
            <div class="device-entity">{{ device.entity_id }}</div>
          </td>

          <!-- Room/Area -->
          <td class="device-area">
            {{ device.area || 'No Area' }}
          </td>

          <!-- Type -->
          <td class="device-type">
            <span class="type-badge" :class="device.device_type || 'broadlink'">
              {{ device.device_type === 'smartir' ? 'SmartIR' : 'Broadlink' }}
            </span>
          </td>

          <!-- Commands -->
          <td class="device-commands">
            <div v-if="(device.device_type || 'broadlink') === 'broadlink'" class="command-list">
              <button 
                v-for="cmd in getDeviceCommands(device)" 
                :key="cmd"
                class="command-btn"
                @click="sendCommand(device, cmd)"
              >
                {{ cmd }}
              </button>
              <span v-if="getDeviceCommands(device).length === 0" class="no-commands">
                No commands
              </span>
            </div>
            <div v-else-if="device.device_type === 'smartir'" class="smartir-info">
              <span class="profile-code">Profile: {{ device.device_code }}</span>
            </div>
          </td>

          <!-- Actions -->
          <td class="device-actions">
            <button class="action-btn edit" @click="editDevice(device)" title="Edit">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
            <button class="action-btn delete" @click="deleteDevice(device)" title="Delete">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'DeviceListView',
  props: {
    devices: {
      type: Array,
      required: true
    }
  },
  methods: {
    getDeviceCommands(device) {
      // Get commands from device metadata
      // Commands are stored as an object with command names as keys
      if (device.commands && typeof device.commands === 'object') {
        return Object.keys(device.commands);
      }
      return [];
    },
    sendCommand(device, command) {
      this.$emit('send-command', { device, command });
    },
    editDevice(device) {
      this.$emit('edit-device', device);
    },
    deleteDevice(device) {
      this.$emit('delete-device', device);
    }
  }
};
</script>

<style scoped>
.device-list-view {
  width: 100%;
  overflow-x: auto;
}

.device-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--ha-card-background, white);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.device-table thead {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
  border-bottom: 2px solid var(--ha-border-color, #e9ecef);
}

.device-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: var(--ha-text-secondary-color, #495057);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.device-table tbody tr {
  border-bottom: 1px solid var(--ha-border-color, #e9ecef);
  transition: background-color 0.2s;
}

.device-table tbody tr:hover {
  background-color: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
}

.device-table td {
  padding: 12px 16px;
  vertical-align: middle;
}

/* Device Info */
.device-info {
  min-width: 200px;
}

.device-name {
  font-weight: 500;
  font-size: 15px;
  color: var(--ha-text-primary-color, #212529);
  margin-bottom: 4px;
}

.device-entity {
  font-size: 12px;
  color: var(--ha-text-secondary-color, #6c757d);
  font-family: 'Courier New', monospace;
}

/* Area */
.device-area {
  color: var(--ha-text-primary-color, #495057);
  font-size: 14px;
}

/* Type Badge */
.type-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.type-badge.broadlink {
  background: #e3f2fd;
  color: #1976d2;
}

.type-badge.smartir {
  background: #f3e5f5;
  color: #7b1fa2;
}

/* Commands */
.device-commands {
  min-width: 250px;
}

.command-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.command-btn {
  padding: 4px 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.command-btn:hover {
  background: #0056b3;
}

.no-commands {
  color: var(--ha-text-secondary-color, #6c757d);
  font-size: 13px;
  font-style: italic;
}

.smartir-info {
  font-size: 13px;
  color: var(--ha-text-primary-color, #495057);
}

.profile-code {
  font-family: 'Courier New', monospace;
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
  padding: 4px 8px;
  border-radius: 4px;
  color: var(--ha-text-primary-color, #495057);
}

/* Actions */
.device-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px;
  background: transparent;
  border: 1px solid var(--ha-border-color, #dee2e6);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ha-text-secondary-color, #6c757d);
}

.action-btn:hover {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
}

.action-btn.edit:hover {
  border-color: var(--ha-primary-color, #007bff);
  color: var(--ha-primary-color, #007bff);
}

.action-btn.delete:hover {
  border-color: #dc3545;
  color: #dc3545;
}

/* Responsive */
@media (max-width: 768px) {
  .device-table {
    font-size: 12px;
  }

  .device-table th,
  .device-table td {
    padding: 8px 12px;
  }

  .command-btn {
    font-size: 11px;
    padding: 3px 8px;
  }
}
</style>
