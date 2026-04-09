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
    async loadDevices(bustCache = false) {
      this.loading = true
      this.error = null
      
      try {
        // Use managed devices endpoint to get devices with proper device_type field
        // Add cache-busting timestamp if requested
        const url = bustCache 
          ? `/api/devices/managed?_t=${Date.now()}` 
          : '/api/devices/managed'
        const response = await api.get(url)
        this.devices = response.data.devices || []
        console.log('📥 Loaded devices:', this.devices)
        this.devices.forEach(device => {
          console.log(`📥 Device "${device.name}":`, {
            id: device.id,
            device: device.device,
            commands: device.commands,
            commandCount: device.commands ? Object.keys(device.commands).length : 0
          })
        })
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
        console.log('🏪 Store: Creating device with data:', deviceData)
        console.log('🏪 Store: Device commands being sent:', deviceData.commands)
        
        // Transform frontend field names to backend expected names
        const backendData = {
          device_name: deviceData.name,
          device: deviceData.device, // Storage name for adopted devices
          area_id: deviceData.area || '',
          area_name: deviceData.area || '',
          entity_type: deviceData.entity_type,
          icon: deviceData.icon,
          broadlink_entity: deviceData.broadlink_entity,
          device_type: deviceData.device_type || 'broadlink',
          commands: deviceData.commands || {},
          brightness_steps: deviceData.brightness_steps
        }
        
        // Add SmartIR config if it's a SmartIR device
        if (deviceData.device_type === 'smartir' && deviceData.smartir_config) {
          backendData.smartir_config = deviceData.smartir_config
        }
        
        console.log('🏪 Store: Transformed data for backend:', backendData)
        
        // Use the new managed devices endpoint that supports device_type
        const response = await api.post('/api/devices/managed', backendData)
        console.log('🏪 Store: Create response:', response.data)
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
    
    async deleteDevice(deviceId, deleteCommands = false, regenerateEntities = false) {
      this.loading = true
      this.error = null
      
      try {
        // Use managed devices endpoint for deletion with optional command deletion and entity regeneration
        // Pass as query parameters (more RESTful for DELETE)
        const params = new URLSearchParams()
        if (deleteCommands) params.append('delete_commands', 'true')
        if (regenerateEntities) params.append('regenerate_entities', 'true')
        
        const url = `/api/devices/managed/${deviceId}${params.toString() ? '?' + params.toString() : ''}`
        await api.delete(url)
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
    },
    
    updateDeviceCommands(deviceId, commands) {
      // Optimistically update device commands in the store
      // This prevents UI lag while waiting for storage file updates (10+ seconds in standalone mode)
      const deviceIndex = this.devices.findIndex(d => d.id === deviceId)
      if (deviceIndex !== -1) {
        // Replace the entire device object to trigger reactivity
        // Vue 3 can track this because we're replacing an array element
        const updatedDevice = {
          ...this.devices[deviceIndex],
          commands: commands
        }
        this.devices.splice(deviceIndex, 1, updatedDevice)
        console.log(`✅ Store: Updated commands for ${deviceId}, count: ${Object.keys(commands).length}`)
      } else {
        console.warn(`⚠️ Store: Device ${deviceId} not found for command update`)
      }
    },
    
    async syncAllAreas(progressCallback = null) {
      console.log('🔄 Starting bulk area sync...')
      
      try {
        // Fetch all managed devices (includes both Broadlink and SmartIR devices)
        const response = await api.get('/api/devices/managed')
        const allDevices = response.data.devices || []
        
        if (allDevices.length === 0) {
          console.log('⚠️ No devices to sync')
          return { synced: 0, total: 0, results: [] }
        }
        
        console.log(`🔄 Syncing areas for ${allDevices.length} devices...`)
        
        // Sync each device's area SEQUENTIALLY to avoid file locking conflicts
        // Network shares can't handle parallel writes to the same file
        const results = []
        for (let i = 0; i < allDevices.length; i++) {
          const device = allDevices[i]
          console.log(`🔄 Syncing device: ${device.id} (${device.name})`)
          
          // Report progress
          if (progressCallback) {
            progressCallback({
              current: i + 1,
              total: allDevices.length,
              deviceName: device.name,
              deviceId: device.id
            })
          }
          
          try {
            const response = await api.post(`/api/devices/${device.id}/sync-area`)
            if (response.data.success && response.data.area) {
              console.log(`✅ Synced area for ${device.name}: ${response.data.area}`)
              results.push({ status: 'synced', device: device.name, area: response.data.area })
            } else {
              results.push({ status: 'no_area', device: device.name })
            }
          } catch (err) {
            // Check if it's a 404 (entity not found in HA)
            if (err.response?.status === 404) {
              console.log(`❌ Device not found in HA: ${device.id}`)
              results.push({ status: 'not_found', device: device.name })
            } else {
              console.warn(`⚠️ Failed to sync area for ${device.id}:`, err.message)
              results.push({ status: 'error', device: device.name, error: err.message })
            }
          }
        }
        
        // Count results
        const syncedCount = results.filter(r => r.status === 'synced').length
        const notFoundCount = results.filter(r => r.status === 'not_found').length
        const errorCount = results.filter(r => r.status === 'error').length
        
        // Wait for file writes to complete (especially important for network shares)
        // The backend writes to devices.json which may be on a network share with write lag
        // Network file system caches can take time to synchronize
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // Reload to show updated areas with cache busting
        await this.loadDevices(true)
        
        console.log(`✅ Area sync complete: ${syncedCount} synced, ${notFoundCount} not found in HA, ${errorCount} errors`)
        
        return {
          synced: syncedCount,
          notFound: notFoundCount,
          errors: errorCount,
          total: allDevices.length,
          results
        }
      } catch (error) {
        console.error('Area sync error:', error)
        throw error
      }
    }
  }
})
