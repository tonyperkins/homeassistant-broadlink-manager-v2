// src/composables/useDeviceStyles.js

import { computed } from 'vue';

export function useDeviceStyles(deviceType) {
  const type = computed(() => deviceType.value || deviceType);

  const icon = computed(() => {
    switch (type.value) {
      case 'climate':
        return 'mdi:air-conditioner';
      case 'fan':
        return 'mdi:fan';
      case 'light':
        return 'mdi:lightbulb';
      case 'media_player':
        return 'mdi:television';
      case 'switch':
        return 'mdi:light-switch';
      default:
        return 'mdi:devices';
    }
  });

  const colorClass = computed(() => {
    return `device-type-${type.value}-color`;
  });

  const tagBgClass = computed(() => {
    return `tag-${type.value}-bg`;
  });

  return {
    icon,
    colorClass,
    tagBgClass,
  };
}
