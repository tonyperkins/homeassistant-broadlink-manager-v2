<template>
  <div class="dashboard">
    <!-- Welcome Banner -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="banner-icon">
          <i class="mdi mdi-rocket-launch"></i>
        </div>
        <div class="banner-text">
          <h2>Welcome to Broadlink Manager v2!</h2>
          <p>Manage your IR/RF devices with a modern Vue 3 interface</p>
        </div>
      </div>
      <div class="status-badges">
        <span class="badge success">
          <i class="mdi mdi-check-circle"></i>
          Vue 3 Ready
        </span>
        <span class="badge warning">
          <i class="mdi mdi-beta"></i>
          Beta
        </span>
      </div>
    </div>

    <!-- Device List Component -->
    <DeviceList />

    <!-- Info Cards -->
    <div class="info-cards">
      <div class="info-card">
        <i class="mdi mdi-information"></i>
        <h3>Development Status</h3>
        <p>This is a beta version. Features are being migrated from v1 incrementally.</p>
      </div>

      <div class="info-card">
        <i class="mdi mdi-github"></i>
        <h3>Repository</h3>
        <p>
          <a href="https://github.com/tonyperkins/homeassistant-broadlink-manager-v2" target="_blank">
            View on GitHub
          </a>
        </p>
      </div>

      <div class="info-card">
        <i class="mdi mdi-bug"></i>
        <h3>Report Issues</h3>
        <p>Found a bug? Please report it on GitHub Issues.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import DeviceList from '@/components/devices/DeviceList.vue'
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100vh;
  position: relative;
  padding-bottom: 200px; /* Space for fixed footer */
}

.welcome-banner {
  background: linear-gradient(135deg, var(--ha-primary-color), #0288d1);
  border-radius: 12px;
  padding: 24px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--ha-shadow-md);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.banner-icon i {
  font-size: 48px;
}

.banner-text h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 500;
}

.banner-text p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.status-badges {
  display: flex;
  gap: 8px;
}

.badge {
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.badge.success {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.badge.warning {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.badge i {
  font-size: 14px;
}

.info-cards {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  padding: 16px;
  background: var(--ha-surface-color);
  border-top: 1px solid var(--ha-border-color);
  z-index: 10;
}

.info-card {
  background: var(--ha-card-background);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid var(--ha-border-color);
}

.info-card i {
  font-size: 32px;
  color: var(--ha-primary-color);
  margin-bottom: 12px;
}

.info-card h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--ha-text-primary-color);
}

.info-card p {
  margin: 0;
  color: var(--ha-text-secondary-color);
  font-size: 14px;
}

.info-card a {
  color: var(--ha-primary-color);
  text-decoration: none;
}

.info-card a:hover {
  text-decoration: underline;
}
</style>
