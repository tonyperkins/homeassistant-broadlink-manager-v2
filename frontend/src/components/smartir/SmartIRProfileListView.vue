<template>
  <div class="profile-list-view">
    <table class="profile-table">
      <thead>
        <tr>
          <th>Code</th>
          <th>Manufacturer</th>
          <th>Model</th>
          <th>Platform</th>
          <th>Controller</th>
          <th>Commands</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="profile in profiles" :key="`${profile.platform}-${profile.code}`" class="profile-row">
          <!-- Code -->
          <td class="profile-code">
            <span class="code-badge">{{ profile.code }}</span>
          </td>

          <!-- Manufacturer -->
          <td class="profile-manufacturer">
            {{ profile.manufacturer || 'Unknown' }}
          </td>

          <!-- Model -->
          <td class="profile-model">
            <div class="model-info">
              <div class="model-name">{{ profile.model || 'Unknown' }}</div>
              <div v-if="profile.models && profile.models.length > 1" class="model-count">
                +{{ profile.models.length - 1 }} more
              </div>
            </div>
          </td>

          <!-- Platform -->
          <td class="profile-platform">
            <span class="platform-badge" :class="profile.platform">
              <i class="mdi" :class="getPlatformIcon(profile.platform)"></i>
              {{ formatPlatform(profile.platform) }}
            </span>
          </td>

          <!-- Controller -->
          <td class="profile-controller">
            {{ profile.controller_brand || 'N/A' }}
          </td>

          <!-- Commands -->
          <td class="profile-commands">
            <div class="command-stats">
              <span class="stat-item">
                <i class="mdi mdi-remote"></i>
                {{ profile.command_count || 0 }}
              </span>
              <span v-if="profile.learned_count > 0" class="stat-item learned">
                <i class="mdi mdi-school"></i>
                {{ profile.learned_count }}
              </span>
            </div>
          </td>

          <!-- Actions -->
          <td class="profile-actions">
            <button class="action-btn edit" @click="editProfile(profile)" title="Edit Profile">
              <i class="mdi mdi-pencil"></i>
            </button>
            <button class="action-btn commands" @click="viewCommands(profile)" title="View Commands">
              <i class="mdi mdi-remote"></i>
            </button>
            <button class="action-btn download" @click="downloadProfile(profile)" title="Download">
              <i class="mdi mdi-download"></i>
            </button>
            <button class="action-btn delete" @click="deleteProfile(profile)" title="Delete">
              <i class="mdi mdi-delete"></i>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'SmartIRProfileListView',
  props: {
    profiles: {
      type: Array,
      required: true
    }
  },
  methods: {
    getPlatformIcon(platform) {
      const icons = {
        climate: 'mdi-thermostat',
        media_player: 'mdi-television',
        fan: 'mdi-fan',
        light: 'mdi-lightbulb'
      };
      return icons[platform] || 'mdi-devices';
    },
    formatPlatform(platform) {
      const names = {
        climate: 'Climate',
        media_player: 'Media Player',
        fan: 'Fan',
        light: 'Light'
      };
      return names[platform] || platform;
    },
    editProfile(profile) {
      this.$emit('edit', profile);
    },
    viewCommands(profile) {
      this.$emit('commands', profile);
    },
    downloadProfile(profile) {
      this.$emit('download', profile);
    },
    deleteProfile(profile) {
      this.$emit('delete', profile);
    }
  }
};
</script>

<style scoped>
.profile-list-view {
  width: 100%;
  overflow-x: auto;
}

.profile-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--ha-card-background, white);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.profile-table thead {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
  border-bottom: 2px solid var(--ha-border-color, #e9ecef);
}

.profile-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: var(--ha-text-secondary-color, #495057);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.profile-table tbody tr {
  border-bottom: 1px solid var(--ha-border-color, #e9ecef);
  transition: background-color 0.2s;
}

.profile-table tbody tr:hover {
  background-color: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
}

.profile-table td {
  padding: 12px 16px;
  vertical-align: middle;
}

/* Code */
.profile-code {
  min-width: 80px;
}

.code-badge {
  display: inline-block;
  padding: 4px 10px;
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
  border: 1px solid var(--ha-border-color, #dee2e6);
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--ha-text-primary-color, #212529);
}

/* Manufacturer */
.profile-manufacturer {
  font-weight: 500;
  color: var(--ha-text-primary-color, #212529);
  min-width: 120px;
}

/* Model */
.profile-model {
  min-width: 150px;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.model-name {
  color: var(--ha-text-primary-color, #212529);
  font-size: 14px;
}

.model-count {
  font-size: 12px;
  color: var(--ha-text-secondary-color, #6c757d);
  font-style: italic;
}

/* Platform Badge */
.profile-platform {
  min-width: 130px;
}

.platform-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
}

.platform-badge.climate {
  background: #e3f2fd;
  color: #1976d2;
}

.platform-badge.media_player {
  background: #f3e5f5;
  color: #7b1fa2;
}

.platform-badge.fan {
  background: #e8f5e9;
  color: #388e3c;
}

.platform-badge.light {
  background: #fff3e0;
  color: #f57c00;
}

/* Controller */
.profile-controller {
  color: var(--ha-text-primary-color, #495057);
  font-size: 14px;
  min-width: 100px;
}

/* Commands */
.profile-commands {
  min-width: 100px;
}

.command-stats {
  display: flex;
  gap: 12px;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--ha-text-secondary-color, #6c757d);
}

.stat-item i {
  font-size: 16px;
}

.stat-item.learned {
  color: #28a745;
}

/* Actions */
.profile-actions {
  display: flex;
  gap: 6px;
  min-width: 180px;
}

.action-btn {
  padding: 6px;
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

.action-btn i {
  font-size: 16px;
}

.action-btn:hover {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
}

.action-btn.edit:hover {
  border-color: var(--ha-primary-color, #007bff);
  color: var(--ha-primary-color, #007bff);
}

.action-btn.commands:hover {
  border-color: #6c757d;
  color: #6c757d;
}

.action-btn.download:hover {
  border-color: #28a745;
  color: #28a745;
}

.action-btn.delete:hover {
  border-color: #dc3545;
  color: #dc3545;
}

/* Responsive */
@media (max-width: 768px) {
  .profile-table {
    font-size: 12px;
  }

  .profile-table th,
  .profile-table td {
    padding: 8px 12px;
  }

  .action-btn {
    padding: 4px;
  }

  .action-btn i {
    font-size: 14px;
  }
}
</style>
