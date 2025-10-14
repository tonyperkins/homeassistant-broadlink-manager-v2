/**
 * SmartIR API Service
 * Handles communication with SmartIR detection endpoints
 */

// Use relative path (no leading slash) for Ingress compatibility
const API_BASE = 'api/smartir';

export const smartirService = {
  /**
   * Get SmartIR installation status
   * @returns {Promise<Object>} Status object with installation info
   */
  async getStatus() {
    try {
      const response = await fetch(`${API_BASE}/status`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching SmartIR status:', error);
      return {
        installed: false,
        version: null,
        error: error.message
      };
    }
  },

  /**
   * Get SmartIR installation instructions
   * @returns {Promise<Object>} Installation instructions
   */
  async getInstallInstructions() {
    try {
      const response = await fetch(`${API_BASE}/install-instructions`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching install instructions:', error);
      throw error;
    }
  },

  /**
   * Get available SmartIR platforms
   * @returns {Promise<Object>} Platforms info
   */
  async getPlatforms() {
    try {
      const response = await fetch(`${API_BASE}/platforms`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching platforms:', error);
      throw error;
    }
  },

  /**
   * Get device codes for a specific platform
   * @param {string} platform - Platform name (climate, media_player, fan)
   * @returns {Promise<Object>} Device codes
   */
  async getPlatformCodes(platform) {
    try {
      const response = await fetch(`${API_BASE}/platforms/${platform}/codes`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching codes for ${platform}:`, error);
      throw error;
    }
  },

  /**
   * Get next available custom code number for a platform
   * @param {string} platform - Platform name
   * @returns {Promise<Object>} Next code info
   */
  async getNextCode(platform) {
    try {
      const response = await fetch(`${API_BASE}/platforms/${platform}/next-code`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching next code for ${platform}:`, error);
      throw error;
    }
  },

  /**
   * Validate a SmartIR code file
   * @param {string} platform - Platform name
   * @param {number} code - Code number
   * @returns {Promise<Object>} Validation result
   */
  async validateCode(platform, code) {
    try {
      const response = await fetch(`${API_BASE}/validate-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ platform, code })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error validating code:', error);
      throw error;
    }
  }
};
