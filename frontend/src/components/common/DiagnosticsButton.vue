<template>
  <div class="diagnostics-container">
    <button @click="showMenu = !showMenu" class="diagnostics-btn" title="Download Diagnostics">
      <i class="mdi mdi-bug"></i>
      Diagnostics
    </button>
    
    <div v-if="showMenu" class="diagnostics-menu">
      <button @click="copyToClipboard" class="menu-item" :disabled="loading">
        <i class="mdi mdi-content-copy"></i>
        Copy Summary
      </button>
      <button @click="downloadBundle" class="menu-item" :disabled="loading">
        <i class="mdi mdi-download"></i>
        Download Full Report
      </button>
      <button @click="showMenu = false" class="menu-item menu-item-cancel">
        <i class="mdi mdi-close"></i>
        Cancel
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const showMenu = ref(false)
const loading = ref(false)

const copyToClipboard = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/diagnostics/markdown')
    const markdown = response.data.markdown
    
    await navigator.clipboard.writeText(markdown)
    toast.success('Diagnostic summary copied to clipboard!')
    showMenu.value = false
  } catch (error) {
    console.error('Error copying diagnostics:', error)
    toast.error('Failed to copy diagnostics')
  } finally {
    loading.value = false
  }
}

const downloadBundle = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/diagnostics/download', {
      responseType: 'blob'
    })
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    // Extract filename from content-disposition header or use default
    const contentDisposition = response.headers['content-disposition']
    let filename = 'broadlink_manager_diagnostics.zip'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    toast.success('Diagnostic bundle downloaded!')
    showMenu.value = false
  } catch (error) {
    console.error('Error downloading diagnostics:', error)
    toast.error('Failed to download diagnostics')
  } finally {
    loading.value = false
  }
}

// Close menu when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.diagnostics-container')) {
    showMenu.value = false
  }
}

// Add/remove event listener
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.diagnostics-container {
  position: relative;
  display: inline-block;
}

.diagnostics-btn {
  background: var(--color-secondary);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.diagnostics-btn:hover {
  background: var(--color-secondary-dark);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.diagnostics-btn:active {
  transform: translateY(0);
}

.diagnostics-btn i {
  font-size: 1.1rem;
}

.diagnostics-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  z-index: 1000;
  overflow: hidden;
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.menu-item {
  width: 100%;
  padding: 0.75rem 1rem;
  border: none;
  background: white;
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  transition: background 0.2s;
  border-bottom: 1px solid var(--color-border-light);
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:hover:not(:disabled) {
  background: var(--color-background-hover);
}

.menu-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-item i {
  font-size: 1.2rem;
  width: 1.2rem;
  text-align: center;
}

.menu-item-cancel {
  color: var(--color-danger);
}

.menu-item-cancel:hover:not(:disabled) {
  background: var(--color-danger-light);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .diagnostics-menu {
    background: var(--color-background-dark);
    border-color: var(--color-border-dark);
  }
  
  .menu-item {
    background: var(--color-background-dark);
    color: var(--color-text-dark);
    border-bottom-color: var(--color-border-dark);
  }
  
  .menu-item:hover:not(:disabled) {
    background: var(--color-background-hover-dark);
  }
}
</style>
