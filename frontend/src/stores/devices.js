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
          commands: deviceData.commands || {}
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
    
    async deleteDevice(deviceId, deleteCommands = false) {
      this.loading = true
      this.error = null
      
      try {
        // Use managed devices endpoint for deletion with optional command deletion
        await api.delete(`/api/devices/managed/${deviceId}`, {
          data: { delete_commands: deleteCommands }
        })
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
    
    async syncAllAreas() {
      // Sync areas from Home Assistant for all devices
      if (!this.devices || this.devices.length === 0) {
        console.log('⚠️ No devices to sync')
        return // Silent return if no devices
      }
      
      console.log(`🔄 Syncing areas from Home Assistant for ${this.devices.length} devices...`)
      
      try {
        // Sync each device's area (in parallel)
        const results = await Promise.all(
          this.devices.map(device => {
            console.log(`🔄 Syncing device: ${device.id} (${device.name})`)
            return api.post(`/api/devices/${device.id}/sync-area`)
              .then(response => {
                if (response.data.success && response.data.area) {
                  console.log(`✅ Synced area for ${device.name}: ${response.data.area}`)
                  return { status: 'synced', device: device.name }
                }
                return { status: 'no_area' }
              })
              .catch(err => {
                // Check if it's a 404 (entity not found in HA)
                if (err.response?.status === 404) {
                  console.log(`❌ Device not found in HA: ${device.id}`)
                  return { status: 'not_found' }
                } else {
                  console.warn(`⚠️ Failed to sync area for ${device.id}:`, err.message)
                  return { status: 'error', error: err.message }
                }
              })
          })
        )
        
        // Count results
        const syncedCount = results.filter(r => r.status === 'synced').length
        const notFoundCount = results.filter(r => r.status === 'not_found').length
        
        // Reload to show updated areas with cache busting
        await this.loadDevices(true)
        
        if (syncedCount > 0) {
          console.log(`✅ Area sync complete: ${syncedCount} synced, ${notFoundCount} not found in HA`)
        } else if (notFoundCount > 0) {
          console.log(`ℹ️ No areas synced - ${notFoundCount} entities not found in HA registry (generate entities first)`)
        }
      } catch (error) {
        // Silent failure - this is a background operation
        console.debug('Area sync error:', error)
      }
    }
  }
})
