import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    loading: false,
    error: null,
    darkMode: false
  }),
  
  actions: {
    setLoading(value) {
      this.loading = value
    },
    
    setError(error) {
      this.error = error
      console.error('App error:', error)
    },
    
    clearError() {
      this.error = null
    },
    
    toggleDarkMode() {
      this.darkMode = !this.darkMode
      document.body.classList.toggle('dark-mode', this.darkMode)
      localStorage.setItem('darkMode', this.darkMode)
    },
    
    loadDarkMode() {
      const saved = localStorage.getItem('darkMode')
      if (saved === 'true') {
        this.darkMode = true
        document.body.classList.add('dark-mode')
      }
    }
  }
})
