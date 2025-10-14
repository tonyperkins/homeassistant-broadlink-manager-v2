# SmartIR Soft Integration - Implementation Plan

## Quick Start (Minimal Viable Integration)

Get SmartIR detection working in **1-2 hours** with these minimal changes:

### Step 1: Backend Detection (30 minutes)

**Files created:**
- ✅ `app/smartir_detector.py` - Detection logic
- ✅ `app/api/smartir.py` - API endpoints

**Integration needed:**

```python
# app/web_server.py - Add to __init__

from smartir_detector import SmartIRDetector
from api.smartir import init_smartir_routes

class BroadlinkWebServer:
    def __init__(self, ...):
        # ... existing code ...
        
        # Initialize SmartIR detector
        self.smartir_detector = SmartIRDetector(config_path="/config")
        
        # Register SmartIR routes
        smartir_bp = init_smartir_routes(self.smartir_detector)
        self.app.register_blueprint(smartir_bp)
        
        # Log SmartIR status on startup
        status = self.smartir_detector.get_status()
        if status["installed"]:
            logger.info(f"✅ SmartIR detected (v{status['version']})")
        else:
            logger.info("ℹ️ SmartIR not detected - climate features limited")
```

### Step 2: Frontend Detection (30 minutes)

**Create: `frontend/src/services/smartir.js`**

```javascript
export const smartirService = {
  async getStatus() {
    const response = await fetch('/api/smartir/status');
    return response.json();
  },
  
  async getInstallInstructions() {
    const response = await fetch('/api/smartir/install-instructions');
    return response.json();
  }
};
```

**Update: `frontend/src/App.vue`**

```vue
<script setup>
import { ref, onMounted } from 'vue';
import { smartirService } from './services/smartir';

const smartirStatus = ref(null);

onMounted(async () => {
  smartirStatus.value = await smartirService.getStatus();
  console.log('SmartIR status:', smartirStatus.value);
});
</script>
```

### Step 3: Simple Banner (30 minutes)

**Create: `frontend/src/components/SmartIRBanner.vue`**

```vue
<template>
  <div v-if="!status?.installed && !dismissed" class="smartir-banner">
    <div class="banner-content">
      <span class="icon">ℹ️</span>
      <div class="message">
        <strong>Want climate device support?</strong>
        Install SmartIR to unlock AC/heater control with temperature and HVAC modes.
      </div>
      <div class="actions">
        <button @click="showGuide" class="btn-primary">Learn More</button>
        <button @click="dismiss" class="btn-text">Dismiss</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  status: Object
});

const dismissed = ref(localStorage.getItem('smartir_banner_dismissed') === 'true');

function dismiss() {
  dismissed.value = true;
  localStorage.setItem('smartir_banner_dismissed', 'true');
}

function showGuide() {
  // Open modal or navigate to guide
  window.open('https://github.com/smartHomeHub/SmartIR', '_blank');
}
</script>

<style scoped>
.smartir-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.icon {
  font-size: 2rem;
}

.message {
  flex: 1;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.btn-primary {
  background: white;
  color: #667eea;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-text {
  background: transparent;
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.5);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

**Add to main view:**

```vue
<!-- frontend/src/components/Dashboard.vue -->
<template>
  <div>
    <SmartIRBanner :status="smartirStatus" />
    <!-- rest of dashboard -->
  </div>
</template>

<script setup>
import SmartIRBanner from './SmartIRBanner.vue';
import { smartirService } from '../services/smartir';

const smartirStatus = ref(null);

onMounted(async () => {
  smartirStatus.value = await smartirService.getStatus();
});
</script>
```

### Step 4: Entity Type Hints (30 minutes)

**Update: Entity type selection component**

```vue
<!-- frontend/src/components/EntityTypeSelector.vue -->
<template>
  <div class="entity-type-selector">
    <label>Entity Type</label>
    <select v-model="selectedType" @change="onTypeChange">
      <option value="light">💡 Light</option>
      <option value="fan">🌀 Fan</option>
      <option value="switch">🔌 Switch</option>
      <option value="media_player">📺 Media Player</option>
      <option value="climate" :disabled="!smartirInstalled">
        🌡️ Climate {{ smartirInstalled ? '' : '(Requires SmartIR)' }}
      </option>
    </select>
    
    <!-- Show warning if climate selected without SmartIR -->
    <div v-if="selectedType === 'climate' && !smartirInstalled" class="warning">
      <p>⚠️ Climate entities require SmartIR integration.</p>
      <a href="#" @click.prevent="showSmartIRGuide">Install SmartIR →</a>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  smartirStatus: Object,
  modelValue: String
});

const emit = defineEmits(['update:modelValue']);

const selectedType = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const smartirInstalled = computed(() => props.smartirStatus?.installed);

function showSmartIRGuide() {
  // Show modal or open guide
  window.open('https://github.com/smartHomeHub/SmartIR', '_blank');
}
</script>

<style scoped>
.warning {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
  color: #856404;
}

.warning a {
  color: #0066cc;
  text-decoration: none;
  font-weight: 600;
}
</style>
```

## That's It for MVP! 🎉

With these 4 simple steps, you have:
- ✅ SmartIR detection working
- ✅ Banner promoting SmartIR (dismissible)
- ✅ Entity type hints
- ✅ Graceful degradation

**Total time: ~2 hours**

## Phase 2: Enhanced Integration (Optional)

Once MVP is working, add these enhancements:

### 1. SmartIR Status Card (1 hour)

```vue
<!-- frontend/src/components/SmartIRStatusCard.vue -->
<template>
  <div class="status-card">
    <h3>🌡️ SmartIR Integration</h3>
    
    <div v-if="status?.installed" class="status-installed">
      <div class="status-badge success">✅ Installed</div>
      <p>Version: {{ status.version }}</p>
      <p>Platforms: {{ status.platforms.join(', ') }}</p>
      <button @click="createProfile" class="btn-primary">
        Create SmartIR Profile
      </button>
    </div>
    
    <div v-else class="status-not-installed">
      <div class="status-badge warning">⚠️ Not Installed</div>
      <p>Install SmartIR to unlock climate device support</p>
      <button @click="showGuide" class="btn-primary">
        View Install Guide
      </button>
    </div>
  </div>
</template>
```

### 2. Install Guide Modal (1 hour)

```vue
<!-- frontend/src/components/SmartIRInstallGuide.vue -->
<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal-content" @click.stop>
      <h2>Install SmartIR</h2>
      
      <div class="benefits">
        <h3>What you'll get:</h3>
        <ul>
          <li>✅ Full climate entity support (AC, heaters)</li>
          <li>✅ Temperature control</li>
          <li>✅ HVAC modes (heat, cool, auto, dry, fan)</li>
          <li>✅ 120+ pre-configured device profiles</li>
        </ul>
      </div>
      
      <div class="methods">
        <h3>Installation Methods:</h3>
        
        <div class="method">
          <h4>HACS (Recommended)</h4>
          <ol>
            <li>Open HACS in Home Assistant</li>
            <li>Go to Integrations</li>
            <li>Click the 3 dots menu → Custom repositories</li>
            <li>Add: <code>https://github.com/smartHomeHub/SmartIR</code></li>
            <li>Category: Integration</li>
            <li>Click "Install"</li>
            <li>Restart Home Assistant</li>
          </ol>
        </div>
        
        <div class="method">
          <h4>Manual Installation</h4>
          <ol>
            <li>Download from GitHub</li>
            <li>Extract to <code>/config/custom_components/smartir</code></li>
            <li>Restart Home Assistant</li>
          </ol>
        </div>
      </div>
      
      <div class="actions">
        <button @click="openGitHub" class="btn-primary">
          Open GitHub
        </button>
        <button @click="close" class="btn-secondary">
          Close
        </button>
      </div>
    </div>
  </div>
</template>
```

### 3. Profile Builder UI (4-6 hours)

This is the big feature - create SmartIR device profiles through UI.

**Components needed:**
- `SmartIRProfileBuilder.vue` - Main builder interface
- `ClimateProfileForm.vue` - Climate-specific form
- `CommandLearningWizard.vue` - Step-by-step learning
- `ProfilePreview.vue` - Show generated JSON

**Flow:**
1. User clicks "Create SmartIR Profile"
2. Select device type (climate, media_player, fan)
3. Enter device info (manufacturer, model)
4. Guided command learning (step-by-step)
5. Preview generated JSON
6. Save to SmartIR directory
7. Generate YAML config

## Testing Checklist

### Without SmartIR
- [ ] App loads without errors
- [ ] Banner shows on first load
- [ ] Banner can be dismissed
- [ ] Climate type shows warning
- [ ] Install guide accessible
- [ ] All other features work

### With SmartIR
- [ ] Auto-detected on startup
- [ ] Version displayed correctly
- [ ] Platform list accurate
- [ ] No warning messages
- [ ] Profile builder accessible (Phase 2)

### Edge Cases
- [ ] SmartIR installed but manifest missing
- [ ] SmartIR installed but no codes directory
- [ ] SmartIR removed after profiles created
- [ ] Multiple page refreshes
- [ ] Banner dismissed then SmartIR installed

## Deployment Strategy

### Release 1: MVP (Detection Only)
- SmartIR detection
- Banner and hints
- No profile builder yet
- Document in README

### Release 2: Profile Builder
- Full SmartIR profile creation
- Climate devices only
- JSON generation
- YAML config generation

### Release 3: Enhanced
- Media player profiles
- Fan profiles
- Profile import/export
- Profile library

## Documentation Updates

### README.md

Add section after "Features":

```markdown
## 🌡️ SmartIR Integration (Optional)

Broadlink Manager integrates seamlessly with [SmartIR](https://github.com/smartHomeHub/SmartIR) 
for advanced climate device support.

**Works great without SmartIR:**
- Learn IR codes for any device
- Create lights, fans, switches, media players
- Full command management

**Even better with SmartIR:**
- Full climate entities (AC, heaters, heat pumps)
- Temperature control and HVAC modes
- 120+ pre-configured device profiles
- Create custom SmartIR profiles through UI

SmartIR is automatically detected - no configuration needed!

[Learn more about SmartIR integration →](docs/SMARTIR_SOFT_INTEGRATION.md)
```

### CHANGELOG.md

```markdown
## [1.11.0] - 2025-XX-XX

### Added
- SmartIR soft integration - automatically detects SmartIR installation
- Contextual guidance for climate device support
- SmartIR status banner (dismissible)
- Entity type hints when SmartIR not installed

### Changed
- Climate entity type now shows SmartIR requirement
- Improved messaging around climate device support
```

## Success Metrics

After implementation, track:
- % of users with SmartIR installed
- Banner dismissal rate
- "Learn More" click rate
- SmartIR installations after seeing banner
- User feedback on integration

## Next Steps

1. **Implement MVP** (Steps 1-4 above) - ~2 hours
2. **Test thoroughly** - Both with and without SmartIR
3. **Deploy to beta** - Get user feedback
4. **Iterate** - Based on feedback
5. **Phase 2** - Profile builder (if users want it)

## Questions to Answer

Before starting Phase 2 (Profile Builder):
- Do users actually want to create SmartIR profiles?
- Or do they just use existing profiles from SmartIR database?
- Is the guided workflow valuable?
- Should we focus on other features instead?

**Recommendation**: Ship MVP first, gather feedback, then decide on Phase 2.
