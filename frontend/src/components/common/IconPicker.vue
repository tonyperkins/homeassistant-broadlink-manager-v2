<template>
  <div class="icon-picker">
    <div class="icon-input-wrapper">
      <input
        :id="inputId"
        v-model="localValue"
        type="text"
        :placeholder="placeholder"
        @input="handleInput"
        @focus="showDropdown = true"
        @blur="handleBlur"
      />
      <div v-if="localValue" class="icon-preview">
        <i :class="`mdi mdi-${localValue.replace('mdi:', '')}`"></i>
      </div>
    </div>
    
    <div v-if="showDropdown && filteredIcons.length > 0" class="icon-dropdown">
      <div class="icon-grid">
        <div
          v-for="icon in filteredIcons"
          :key="icon"
          class="icon-option"
          @mousedown.prevent="selectIcon(icon)"
          :title="icon"
        >
          <i :class="`mdi mdi-${icon}`"></i>
          <span>{{ icon }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  inputId: {
    type: String,
    default: 'icon-input'
  },
  placeholder: {
    type: String,
    default: 'e.g., mdi:television'
  }
})

const emit = defineEmits(['update:modelValue'])

const localValue = ref(props.modelValue)
const showDropdown = ref(false)

// Comprehensive Home Assistant icon list
const commonIcons = [
  // Media & Entertainment
  'television', 'speaker', 'radio', 'music', 'video', 'movie', 'play', 'pause', 'stop',
  'skip-next', 'skip-previous', 'volume-high', 'volume-medium', 'volume-low', 'volume-off',
  'remote', 'remote-tv', 'cast', 'chromecast', 'spotify', 'netflix', 'youtube',
  
  // Lights
  'lightbulb', 'lightbulb-on', 'lightbulb-off', 'lamp', 'floor-lamp', 'ceiling-light',
  'light-switch', 'led-strip', 'led-strip-variant', 'wall-sconce', 'chandelier',
  'spotlight', 'track-light', 'vanity-light', 'desk-lamp',
  
  // Climate
  'fan', 'ceiling-fan', 'air-conditioner', 'thermometer', 'thermostat', 'heat-wave',
  'snowflake', 'fire', 'radiator', 'water-boiler', 'hvac',
  
  // Covers & Blinds
  'blinds', 'blinds-open', 'window-shutter', 'window-shutter-open', 'curtains',
  'curtains-closed', 'roller-shade', 'roller-shade-closed', 'garage', 'garage-open',
  'gate', 'door', 'door-open', 'window-open', 'window-closed',
  
  // Appliances
  'washing-machine', 'tumble-dryer', 'dishwasher', 'refrigerator', 'stove',
  'microwave', 'oven', 'toaster', 'kettle', 'coffee', 'coffee-maker', 'blender',
  
  // Vacuum & Cleaning
  'robot-vacuum', 'robot-vacuum-variant', 'vacuum', 'broom', 'spray-bottle',
  
  // Security & Safety
  'lock', 'lock-open', 'lock-smart', 'key', 'shield', 'shield-check', 'alarm-light',
  'bell', 'doorbell', 'camera', 'cctv', 'motion-sensor', 'smoke-detector',
  'fire-extinguisher', 'water-alert', 'gas-cylinder',
  
  // Furniture & Rooms
  'sofa', 'bed', 'bed-double', 'desk', 'chair', 'table', 'bookshelf',
  'home', 'home-outline', 'home-assistant', 'floor-plan', 'room',
  
  // Weather
  'weather-sunny', 'weather-night', 'weather-cloudy', 'weather-rainy', 'weather-snowy',
  'weather-lightning', 'weather-windy', 'weather-fog', 'weather-partly-cloudy',
  'umbrella', 'water', 'water-percent',
  
  // Tech & Devices
  'phone', 'cellphone', 'tablet', 'laptop', 'desktop-tower', 'monitor', 'keyboard',
  'mouse', 'printer', 'router', 'router-wireless', 'access-point', 'wifi',
  'bluetooth', 'usb', 'hdmi-port', 'ethernet',
  
  // Power & Energy
  'power', 'power-plug', 'power-socket', 'battery', 'battery-charging',
  'lightning-bolt', 'flash', 'solar-panel', 'solar-power',
  
  // Nature & Garden
  'leaf', 'tree', 'flower', 'sprout', 'grass', 'watering-can', 'shovel',
  'fence', 'pool', 'hot-tub',
  
  // Kitchen & Dining
  'silverware', 'silverware-fork-knife', 'food', 'food-apple', 'glass-wine',
  'glass-cocktail', 'bottle-wine', 'pot', 'pot-steam',
  
  // Bathroom
  'shower', 'shower-head', 'bathtub', 'toilet', 'sink', 'faucet', 'hand-wash',
  
  // Garage & Tools
  'car', 'car-side', 'garage-variant', 'tools', 'hammer', 'wrench', 'screwdriver',
  'toolbox', 'ladder',
  
  // Health & Fitness
  'heart', 'heart-pulse', 'run', 'walk', 'bike', 'dumbbell', 'yoga',
  'scale-bathroom', 'thermometer-lines',
  
  // Time & Calendar
  'clock', 'clock-outline', 'timer', 'alarm', 'calendar', 'calendar-today',
  'calendar-clock', 'history',
  
  // Notifications & Alerts
  'bell-ring', 'bell-alert', 'alert', 'alert-circle', 'information', 'help-circle',
  'check', 'check-circle', 'close-circle', 'minus-circle', 'plus-circle',
  
  // Navigation & Controls
  'arrow-up', 'arrow-down', 'arrow-left', 'arrow-right', 'chevron-up', 'chevron-down',
  'menu', 'dots-vertical', 'dots-horizontal', 'cog', 'tune',
  
  // Shapes & Symbols
  'circle', 'square', 'triangle', 'hexagon', 'star', 'star-outline',
  'heart-outline', 'plus', 'minus', 'close', 'check-bold',
  
  // Miscellaneous
  'eye', 'eye-off', 'account', 'account-group', 'baby', 'dog', 'cat', 'paw',
  'gift', 'balloon', 'party-popper', 'candle', 'book', 'book-open',
  'newspaper', 'email', 'message', 'phone-classic'
]

watch(() => props.modelValue, (newVal) => {
  localValue.value = newVal
})

const filteredIcons = computed(() => {
  if (!localValue.value) return commonIcons.slice(0, 50)
  
  const searchTerm = localValue.value.toLowerCase().replace('mdi:', '')
  return commonIcons.filter(icon => 
    icon.toLowerCase().includes(searchTerm)
  ).slice(0, 50)
})

const handleInput = () => {
  showDropdown.value = true
  emit('update:modelValue', localValue.value)
}

const handleBlur = () => {
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}

const selectIcon = (icon) => {
  localValue.value = `mdi:${icon}`
  emit('update:modelValue', localValue.value)
  showDropdown.value = false
}
</script>

<style scoped>
.icon-picker {
  position: relative;
}

.icon-input-wrapper {
  position: relative;
}

.icon-input-wrapper input {
  width: 100%;
  padding-right: 40px;
}

.icon-preview {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

.icon-preview i {
  font-size: 20px;
  color: var(--ha-primary-color);
}

.icon-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 4px;
  padding: 8px;
}

.icon-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.icon-option:hover {
  background: var(--ha-hover-color);
  border-color: var(--ha-primary-color);
}

.icon-option i {
  font-size: 24px;
  color: var(--ha-text-primary-color);
}

.icon-option span {
  font-size: 10px;
  color: var(--ha-text-secondary-color);
  text-align: center;
  word-break: break-word;
  max-width: 100%;
}
</style>
