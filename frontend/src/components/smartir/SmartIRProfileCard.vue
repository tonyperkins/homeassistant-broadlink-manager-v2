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
        <div class="profile-stats" :title="profile.commandCount + ' total commands' + (profile.learnedCount > 0 ? ', ' + profile.learnedCount + ' learned' : '')">
          <i class="mdi mdi-remote"></i>
          <span>{{ profile.commandCount }} command{{ profile.commandCount !== 1 ? 's' : '' }}</span>
          <span v-if="profile.learnedCount > 0" class="learned-indicator">( {{ profile.learnedCount }} learned )</span>
        </div>
        <div class="profile-actions">
            <button @click="$emit('commands')" class="action-btn" title="Commands">
                <i class="mdi mdi-remote-tv"></i>
            </button>
            <button 
              v-if="isWizardCompatible" 
              @click="$emit('edit')" 
              class="action-btn" 
              title="Edit Profile"
            >
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

defineEmits(['edit', 'download', 'delete', 'commands']);

const styles = useDeviceStyles(computed(() => props.profile.platform));

// Check if profile is wizard-compatible (can be edited in wizard)
// For now, we assume profiles created by the wizard have a wizardCreated flag
// In the future, we could add more sophisticated structure validation
const isWizardCompatible = computed(() => {
  return props.profile.wizardCreated === true
})

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
@import '@/assets/css/card-styles.css';

/* Card base, header, and icon styles imported from card-styles.css */

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

/* Icon colors, details, meta, stats, and tags imported from card-styles.css */

.profile-stats {
  margin-top: 6px;
  font-size: 13px;
}

.profile-stats i {
  font-size: 16px;
}

.platform-tag {
  background: var(--ha-secondary-background-color) !important;
  color: var(--ha-secondary-text-color) !important;
}

/* Tag backgrounds imported from card-styles.css */

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

/* Footer styles imported from card-styles.css */

.profile-card-footer {
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

/* Actions and buttons imported from card-styles.css */

/* Delete button hover imported from card-styles.css */
</style>
