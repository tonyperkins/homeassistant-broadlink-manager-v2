import { getCurrentInstance } from 'vue'

// Track if we've already warned about toast not being available
let hasWarnedAboutToast = false

export function useToast() {
  const instance = getCurrentInstance()
  const toast = instance?.appContext.config.globalProperties.$toast
  
  if (!toast) {
    // Only warn once to avoid console spam
    if (!hasWarnedAboutToast) {
      console.warn('Toast notification system not yet initialized - using console fallback')
      hasWarnedAboutToast = true
    }
    return {
      success: (msg) => console.log('✓', msg),
      error: (msg) => console.error('✗', msg),
      warning: (msg) => console.warn('⚠', msg),
      info: (msg) => console.info('ℹ', msg)
    }
  }
  
  return toast
}
