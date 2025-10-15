import { defineStore } from 'pinia'
import api from '@/services/api'

export const useDeviceStore = defineStore('devices', {
  state: () => ({
    devices: [],
    loading: false,
    error: null,
    selectedDevice: null
  }),
  
  getters: {
    deviceById: (state) => (id) => {
      return state.devices.find(d => d.id === id)
    },
    
    devicesByType: (state) => (type) => {
      return state.devices.filter(d => d.entity_type === type)
    },
    
    deviceCount: (state) => state.devices.length,
    
    hasDevices: (state) => state.devices.length > 0
  },
  
  actions: {
    async loadDevices() {
      this.loading = true
      this.error = null
      
      try {
        // Use managed devices endpoint to get devices with proper device_type field
        const response = await api.get('/api/devices/managed')
        this.devices = response.data.devices || []
        console.log('Loaded devices:', this.devices)
      } catch (error) {
        this.error = error.message
        console.error('Error loading devices:', error)
      } finally {
        this.loading = false
      }
    },
    
    async createDevice(deviceData) {
      this.loading = true
      this.error = null
      
      try {
        // Use the new managed devices endpoint that supports device_type
        const response = await api.post('/api/devices/managed', deviceData)
        await this.loadDevices() // Reload list
        return response.data
      } catch (error) {
        // Don't set this.error - let the component handle it with ErrorDialog
        console.error('Error creating device:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async updateDevice(deviceId, deviceData) {
      this.loading = true
      this.error = null
      
      try {
        // Use managed devices endpoint for updates
        const response = await api.put(`/api/devices/managed/${deviceId}`, deviceData)
        await this.loadDevices() // Reload list
        return response.data
      } catch (error) {
        // Don't set this.error - let the component handle it with ErrorDialog
        console.error('Error updating device:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async deleteDevice(deviceId) {
      this.loading = true
      this.error = null
      
      try {
        // Use managed devices endpoint for deletion
        await api.delete(`/api/devices/managed/${deviceId}`)
        this.devices = this.devices.filter(d => d.id !== deviceId)
      } catch (error) {
        this.error = error.message
        console.error('Error deleting device:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    selectDevice(device) {
      this.selectedDevice = device
    },
    
    clearSelection() {
      this.selectedDevice = null
    },
    
    clearError() {
      this.error = null
    }
  }
})
