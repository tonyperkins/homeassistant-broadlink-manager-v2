import { getCurrentInstance } from 'vue'

export function useToast() {
  const instance = getCurrentInstance()
  const toast = instance?.appContext.config.globalProperties.$toast
  
  if (!toast) {
    console.warn('Toast not available')
    return {
      success: (msg) => console.log('Success:', msg),
      error: (msg) => console.error('Error:', msg),
      warning: (msg) => console.warn('Warning:', msg),
      info: (msg) => console.info('Info:', msg)
    }
  }
  
  return toast
}
