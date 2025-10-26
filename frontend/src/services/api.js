import axios from 'axios'

// Use relative base URL for Ingress compatibility
// When accessed via Ingress, requests will be relative to the ingress path
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || './',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Global error handling
    console.error('API Error:', error)
    
    if (error.response) {
      // Server responded with error status
      console.error('Response error:', error.response.data)
    } else if (error.request) {
      // Request made but no response
      console.error('No response received')
    } else {
      // Error setting up request
      console.error('Request setup error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default api
