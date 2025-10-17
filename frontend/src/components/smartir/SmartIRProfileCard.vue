<template>
  <div class="profile-card">
    <div class="profile-card-header">
      <div class="profile-icon" :class="styles.colorClass.value" :title="formatPlatformName(profile.platform)">
        <i :class="getIconClass(styles.icon.value)"></i>
      </div>
      <div class="profile-details">
        <h4 :title="`${profile.manufacturer} ${profile.model}`">{{ profile.manufacturer }} {{ profile.model }}</h4>
        <div class="profile-meta">
          <span class="tag platform-tag" :title="formatPlatformName(profile.platform)">
            {{ formatPlatformName(profile.platform) }}
          </span>
          <span v-if="profile.controllerBrand" class="tag controller-tag" :class="getControllerClass(profile.controllerBrand)" :title="'Controller: ' + profile.controllerBrand">
            <i class="mdi mdi-remote-tv"></i>
            {{ profile.controllerBrand }}
          </span>
        </div>
      </div>
      <div class="code-badge" :title="'Device Code: ' + profile.code">{{ profile.code }}</div>
    </div>
    <div class="profile-card-footer">
        <div class="command-info" :title="profile.commandCount + ' total commands' + (profile.learnedCount > 0 ? ', ' + profile.learnedCount + ' learned' : '')">
            <i class="mdi mdi-remote"></i>
            <span>{{ profile.commandCount }} command{{ profile.commandCount !== 1 ? 's' : '' }}</span>
            <span v-if="profile.learnedCount > 0" class="learned-indicator">( {{ profile.learnedCount }} learned )</span>
        </div>
        <div class="profile-actions">
            <button @click="$emit('edit')" class="action-btn" title="Edit Profile">
                <i class="mdi mdi-pencil"></i>
            </button>
            <button @click="$emit('download')" class="action-btn" title="Download JSON">
                <i class="mdi mdi-download"></i>
            </button>
            <button @click="$emit('delete')" class="action-btn delete" title="Delete Profile">
                <i class="mdi mdi-delete"></i>
            </button>
        </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useDeviceStyles } from '@/composables/useDeviceStyles.js';

const props = defineProps({
  profile: {
    type: Object,
    required: true,
  },
});

defineEmits(['edit', 'download', 'delete']);

const styles = useDeviceStyles(computed(() => props.profile.platform));

const formatPlatformName = (platform) => {
  return platform.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

const getIconClass = (icon) => {
  // Convert mdi:icon-name to mdi mdi-icon-name
  if (icon && icon.startsWith('mdi:')) {
    return `mdi ${icon.replace(':', ' mdi-')}`;
  }
  return `mdi mdi-${icon}`;
};

const getControllerClass = (brand) => {
  if (!brand) return '';
  const brandLower = brand.toLowerCase();
  if (brandLower.includes('broadlink')) {
    return 'broadlink-tag';
  } else if (brandLower.includes('not set')) {
    return 'not-set-tag';
  }
  return 'default-controller-tag';
};

</script>

<style scoped>
@import '@/assets/css/variables.css';

.profile-card {
  background: var(--ha-card-background);
  border: 1px solid var(--ha-divider-color);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.2s;
}

.profile-card:hover {
  box-shadow: var(--ha-shadow-md);
  border-color: var(--ha-primary-color);
}

.profile-card-header {
  display: flex;
  gap: 12px;
  position: relative;
}

.profile-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(127, 127, 127, 0.1);
  border-radius: 50%;
  cursor: help;
}

.profile-icon i {
  font-size: 24px;
}

.code-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: var(--ha-secondary-background-color);
  color: var(--ha-secondary-text-color);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  font-family: monospace;
  cursor: help;
  transition: all 0.2s;
}

.code-badge:hover {
  background: var(--ha-primary-color);
  color: white;
  transform: scale(1.05);
}

.device-type-climate-color i { color: var(--device-type-climate-color); }
.device-type-fan-color i { color: var(--device-type-fan-color); }
.device-type-light-color i { color: var(--device-type-light-color); }
.device-type-media-player-color i { color: var(--device-type-media-player-color); }
.device-type-switch-color i { color: var(--device-type-switch-color); }

.profile-details {
  flex: 1;
  min-width: 0;
}

.profile-details h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ha-text-primary-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: help;
}

.profile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  text-transform: capitalize;
  cursor: help;
}

.platform-tag {
  background: var(--ha-secondary-background-color) !important;
  color: var(--ha-secondary-text-color) !important;
}

/* Remove colored backgrounds - all tags use same neutral style */
.tag-climate-bg,
.tag-fan-bg,
.tag-light-bg,
.tag-media-player-bg,
.tag-switch-bg {
  background: var(--ha-secondary-background-color) !important;
  color: var(--ha-secondary-text-color) !important;
}

.code-tag {
  background: var(--ha-secondary-background-color) !important;
  color: var(--ha-secondary-text-color) !important;
}

.controller-tag {
  background: var(--ha-secondary-background-color) !important;
  color: var(--ha-secondary-text-color) !important;
}

.broadlink-tag {
  background: var(--ha-secondary-background-color) !important;
  color: var(--ha-secondary-text-color) !important;
}

.not-set-tag {
  background-color: var(--tag-not-set-bg);
  color: var(--tag-not-set-color);
}

.default-controller-tag {
    background-color: var(--tag-default-bg);
    color: var(--ha-text-primary-color);
}

.profile-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 12px;
    border-top: 1px solid var(--ha-divider-color);
    font-size: 13px;
    color: var(--ha-secondary-text-color);
}

.command-info {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: help;
}

.learned-indicator {
    font-style: italic;
    opacity: 0.8;
}

.profile-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  background: transparent;
  border: 1px solid var(--ha-border-color);
  color: var(--ha-text-primary-color);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn i {
  font-size: 18px;
}

.action-btn:hover {
  background: var(--ha-primary-color);
  color: white;
  border-color: var(--ha-primary-color);
}

.action-btn.delete:hover {
  background: var(--ha-error-color);
  color: white;
  border-color: var(--ha-error-color);
}
</style>
