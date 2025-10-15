<template>
  <div class="searchable-dropdown" ref="dropdownRef">
    <label v-if="label" class="dropdown-label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    
    <div class="dropdown-input-wrapper" :class="{ 'has-error': error, 'disabled': disabled }">
      <input
        ref="inputRef"
        type="text"
        v-model="searchQuery"
        :placeholder="placeholder"
        :disabled="disabled || loading"
        @focus="handleFocus"
        @blur="handleBlur"
        @keydown.down.prevent="navigateDown"
        @keydown.up.prevent="navigateUp"
        @keydown.enter.prevent="selectHighlighted"
        @keydown.escape="closeDropdown"
        class="dropdown-input"
      />
      
      <div class="dropdown-icons">
        <i v-if="loading" class="mdi mdi-loading mdi-spin"></i>
        <i v-else-if="modelValue && !disabled" 
           class="mdi mdi-close-circle clear-icon" 
           @click="clearSelection"
        ></i>
        <i v-else class="mdi mdi-chevron-down"></i>
      </div>
    </div>
    
    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="hint && !error" class="hint-message">{{ hint }}</div>
    
    <Transition name="dropdown">
      <div v-if="isOpen && filteredOptions.length > 0" class="dropdown-menu">
        <div
          v-for="(option, index) in filteredOptions"
          :key="getOptionValue(option)"
          class="dropdown-item"
          :class="{ 
            'highlighted': index === highlightedIndex,
            'selected': isSelected(option)
          }"
          @mousedown.prevent="selectOption(option)"
          @mouseenter="highlightedIndex = index"
        >
          <div class="option-content">
            <div class="option-label">{{ getOptionLabel(option) }}</div>
            <div v-if="getOptionDescription(option)" class="option-description">
              {{ getOptionDescription(option) }}
            </div>
          </div>
          <i v-if="isSelected(option)" class="mdi mdi-check selected-icon"></i>
        </div>
      </div>
    </Transition>
    
    <div v-if="isOpen && filteredOptions.length === 0 && !loading" class="dropdown-menu">
      <div class="dropdown-item no-results">
        <i class="mdi mdi-magnify"></i>
        No results found
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number, Object],
    default: null
  },
  options: {
    type: Array,
    required: true,
    default: () => []
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Search...'
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  },
  // For object options
  optionLabel: {
    type: String,
    default: 'label'
  },
  optionValue: {
    type: String,
    default: 'value'
  },
  optionDescription: {
    type: String,
    default: 'description'
  },
  // Filter function
  filterMethod: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'search'])

const dropdownRef = ref(null)
const inputRef = ref(null)
const searchQuery = ref('')
const isOpen = ref(false)
const highlightedIndex = ref(0)
const isFocused = ref(false)

// Get option label (supports both string and object options)
const getOptionLabel = (option) => {
  if (typeof option === 'string' || typeof option === 'number') {
    return option
  }
  return option[props.optionLabel] || option.label || option.name || String(option)
}

// Get option value
const getOptionValue = (option) => {
  if (typeof option === 'string' || typeof option === 'number') {
    return option
  }
  return option[props.optionValue] || option.value || option.id || option
}

// Get option description
const getOptionDescription = (option) => {
  if (typeof option === 'string' || typeof option === 'number') {
    return ''
  }
  return option[props.optionDescription] || option.description || ''
}

// Check if option is selected
const isSelected = (option) => {
  const optionValue = getOptionValue(option)
  if (typeof props.modelValue === 'object') {
    return getOptionValue(props.modelValue) === optionValue
  }
  return props.modelValue === optionValue
}

// Filter options based on search query
const filteredOptions = computed(() => {
  if (!searchQuery.value) {
    return props.options
  }
  
  // Use custom filter method if provided
  if (props.filterMethod) {
    return props.options.filter(option => 
      props.filterMethod(option, searchQuery.value)
    )
  }
  
  // Default filter: case-insensitive search in label and description
  const query = searchQuery.value.toLowerCase()
  return props.options.filter(option => {
    const label = getOptionLabel(option).toLowerCase()
    const description = getOptionDescription(option).toLowerCase()
    return label.includes(query) || description.includes(query)
  })
})

// Get display value for input
const displayValue = computed(() => {
  if (!props.modelValue) return ''
  
  // Find the option that matches the model value
  const option = props.options.find(opt => {
    const optValue = getOptionValue(opt)
    if (typeof props.modelValue === 'object') {
      return optValue === getOptionValue(props.modelValue)
    }
    return optValue === props.modelValue
  })
  
  return option ? getOptionLabel(option) : ''
})

// Watch for model value changes
watch(() => props.modelValue, (newValue) => {
  if (!isFocused.value) {
    searchQuery.value = displayValue.value
  }
})

// Watch for options changes (e.g., when models are loaded)
watch(() => props.options, () => {
  if (!isFocused.value && props.modelValue) {
    searchQuery.value = displayValue.value
  }
}, { deep: true })

// Watch search query for search event
watch(searchQuery, (newValue) => {
  emit('search', newValue)
  highlightedIndex.value = 0
})

// Initialize search query with display value
onMounted(() => {
  searchQuery.value = displayValue.value
})

const handleFocus = () => {
  isFocused.value = true
  isOpen.value = true
  // Select all text on focus for easy replacement
  inputRef.value?.select()
}

const handleBlur = () => {
  isFocused.value = false
  // Delay to allow click on dropdown item
  setTimeout(() => {
    isOpen.value = false
    // Restore display value if nothing selected
    if (!props.modelValue) {
      searchQuery.value = ''
    } else {
      searchQuery.value = displayValue.value
    }
  }, 200)
}

const closeDropdown = () => {
  isOpen.value = false
  inputRef.value?.blur()
}

const selectOption = (option) => {
  const value = getOptionValue(option)
  emit('update:modelValue', value)
  emit('change', value, option)
  searchQuery.value = getOptionLabel(option)
  closeDropdown()
}

const clearSelection = () => {
  emit('update:modelValue', null)
  emit('change', null, null)
  searchQuery.value = ''
  inputRef.value?.focus()
}

const navigateDown = () => {
  if (!isOpen.value) {
    isOpen.value = true
    return
  }
  if (highlightedIndex.value < filteredOptions.value.length - 1) {
    highlightedIndex.value++
  }
}

const navigateUp = () => {
  if (highlightedIndex.value > 0) {
    highlightedIndex.value--
  }
}

const selectHighlighted = () => {
  if (filteredOptions.value.length > 0 && highlightedIndex.value >= 0) {
    selectOption(filteredOptions.value[highlightedIndex.value])
  }
}

// Click outside to close
const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isOpen.value = false
    if (!props.modelValue) {
      searchQuery.value = ''
    } else {
      searchQuery.value = displayValue.value
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.searchable-dropdown {
  position: relative;
  width: 100%;
}

.dropdown-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--ha-text-primary-color);
  font-size: 14px;
}

.required {
  color: var(--ha-error-color, #f44336);
  margin-left: 2px;
}

.dropdown-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.dropdown-input {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 1px solid var(--ha-divider-color, #e0e0e0);
  border-radius: 8px;
  font-size: 14px;
  background: var(--ha-card-background);
  color: var(--ha-text-primary-color);
  transition: all 0.2s;
}

.dropdown-input:focus {
  outline: none;
  border-color: var(--ha-primary-color, #03a9f4);
  box-shadow: 0 0 0 3px rgba(3, 169, 244, 0.1);
}

.dropdown-input:disabled {
  background: var(--ha-disabled-background, #f5f5f5);
  cursor: not-allowed;
  opacity: 0.6;
}

.dropdown-input-wrapper.has-error .dropdown-input {
  border-color: var(--ha-error-color, #f44336);
}

.dropdown-input-wrapper.has-error .dropdown-input:focus {
  box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.1);
}

.dropdown-input-wrapper.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dropdown-icons {
  position: absolute;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  pointer-events: none;
}

.dropdown-icons i {
  font-size: 20px;
  color: var(--ha-text-secondary-color);
}

.clear-icon {
  pointer-events: all;
  cursor: pointer;
  transition: color 0.2s;
}

.clear-icon:hover {
  color: var(--ha-error-color, #f44336);
}

.mdi-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-message {
  margin-top: 6px;
  font-size: 12px;
  color: var(--ha-error-color, #f44336);
}

.hint-message {
  margin-top: 6px;
  font-size: 12px;
  color: var(--ha-text-secondary-color);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 300px;
  overflow-y: auto;
  background: var(--ha-card-background);
  border: 1px solid var(--ha-divider-color, #e0e0e0);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.dropdown-item {
  padding: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  transition: background 0.2s;
  border-bottom: 1px solid var(--ha-divider-color, #e0e0e0);
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover,
.dropdown-item.highlighted {
  background: var(--ha-hover-background, rgba(0, 0, 0, 0.05));
}

.dropdown-item.selected {
  background: rgba(3, 169, 244, 0.1);
}

.dropdown-item.no-results {
  color: var(--ha-text-secondary-color);
  cursor: default;
  justify-content: center;
  gap: 8px;
}

.dropdown-item.no-results:hover {
  background: transparent;
}

.option-content {
  flex: 1;
  min-width: 0;
}

.option-label {
  font-size: 14px;
  color: var(--ha-text-primary-color);
  font-weight: 500;
}

.option-description {
  font-size: 12px;
  color: var(--ha-text-secondary-color);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-icon {
  color: var(--ha-primary-color, #03a9f4);
  font-size: 20px;
  flex-shrink: 0;
}

/* Dropdown animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Custom scrollbar */
.dropdown-menu::-webkit-scrollbar {
  width: 8px;
}

.dropdown-menu::-webkit-scrollbar-track {
  background: transparent;
}

.dropdown-menu::-webkit-scrollbar-thumb {
  background: var(--ha-divider-color, #e0e0e0);
  border-radius: 4px;
}

.dropdown-menu::-webkit-scrollbar-thumb:hover {
  background: var(--ha-text-secondary-color);
}
</style>
