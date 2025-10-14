# SmartIR Integration - Quick Start

## TL;DR

**Goal**: Broadlink Manager works with or without SmartIR. Auto-detect and guide users.

**Time**: 2 hours for MVP

**Files Ready**: 
- ✅ `app/smartir_detector.py`
- ✅ `app/api/smartir.py`

**What You Build**:
1. Integrate detector into web server
2. Add frontend status check
3. Show banner when SmartIR not installed
4. Add hints in entity type selector

## Copy-Paste Implementation

### 1. Backend Integration (app/web_server.py)

Add these imports at the top:
```python
from smartir_detector import SmartIRDetector
from api.smartir import init_smartir_routes
```

Add to `__init__` method:
```python
# Initialize SmartIR detector
self.smartir_detector = SmartIRDetector(config_path="/config")

# Register SmartIR routes
smartir_bp = init_smartir_routes(self.smartir_detector)
self.app.register_blueprint(smartir_bp)

# Log SmartIR status
status = self.smartir_detector.get_status()
if status["installed"]:
    logger.info(f"✅ SmartIR detected (v{status['version']})")
else:
    logger.info("ℹ️ SmartIR not detected - climate features limited")
```

### 2. Frontend Service (frontend/src/services/smartir.js)

Create new file:
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

### 3. App State (frontend/src/App.vue)

Add to script:
```javascript
import { smartirService } from './services/smartir';

const smartirStatus = ref(null);

onMounted(async () => {
  smartirStatus.value = await smartirService.getStatus();
  console.log('SmartIR:', smartirStatus.value.installed ? '✅' : '❌');
});

// Provide to child components
provide('smartirStatus', smartirStatus);
```

### 4. Banner Component (frontend/src/components/SmartIRBanner.vue)

Create new file - see full code in SMARTIR_IMPLEMENTATION_PLAN.md

Key features:
- Shows when SmartIR not installed
- Dismissible (localStorage)
- Links to install guide

### 5. Entity Type Hints

Update entity type selector:
```vue
<option value="climate" :disabled="!smartirInstalled">
  🌡️ Climate {{ smartirInstalled ? '' : '(Requires SmartIR)' }}
</option>

<div v-if="selectedType === 'climate' && !smartirInstalled" class="warning">
  ⚠️ Climate entities require SmartIR.
  <a @click="showGuide">Install SmartIR →</a>
</div>
```

## Test It

### Without SmartIR
```bash
# Make sure SmartIR is not installed
ls /config/custom_components/smartir  # Should not exist

# Start Broadlink Manager
# Check logs: "ℹ️ SmartIR not detected"
# Open UI: Banner should show
# Try climate type: Should show warning
```

### With SmartIR
```bash
# Install SmartIR via HACS
# Restart HA
# Start Broadlink Manager
# Check logs: "✅ SmartIR detected (v1.17.9)"
# Open UI: No banner, climate type enabled
```

## API Endpoints

Test with curl:
```bash
# Check status
curl http://localhost:8099/api/smartir/status

# Get install instructions
curl http://localhost:8099/api/smartir/install-instructions

# Get platforms (if installed)
curl http://localhost:8099/api/smartir/platforms
```

## Troubleshooting

**Banner doesn't show**
- Check localStorage: `smartir_banner_dismissed`
- Clear it: `localStorage.removeItem('smartir_banner_dismissed')`

**Status always shows not installed**
- Check path: `/config/custom_components/smartir`
- Check manifest exists: `/config/custom_components/smartir/manifest.json`
- Check logs for errors

**Climate type not disabled**
- Check `smartirStatus` is provided to component
- Check computed property: `smartirInstalled`
- Console log the status

## What Users See

### Scenario 1: No SmartIR
```
┌─────────────────────────────────────────────┐
│ ℹ️ Want climate device support?            │
│ Install SmartIR to unlock AC/heater control │
│ [Learn More] [Dismiss]                      │
└─────────────────────────────────────────────┘

Entity Type: [Dropdown ▼]
  • Light
  • Fan  
  • Switch
  • Media Player
  • Climate (Requires SmartIR) ← Disabled
```

### Scenario 2: SmartIR Installed
```
✅ SmartIR v1.17.9 detected

Entity Type: [Dropdown ▼]
  • Light
  • Fan
  • Switch
  • Media Player
  • Climate ← Enabled
```

## Documentation

Update README.md:
```markdown
## SmartIR Integration (Optional)

Broadlink Manager integrates with SmartIR for climate device support.

- **Without SmartIR**: Learn IR codes, create lights/fans/switches
- **With SmartIR**: All above + full climate entities (AC, heaters)

SmartIR is auto-detected - no configuration needed!
```

## Deployment Checklist

- [ ] Backend integration complete
- [ ] Frontend service created
- [ ] Banner component added
- [ ] Entity type hints updated
- [ ] Tested without SmartIR
- [ ] Tested with SmartIR
- [ ] Tested transition (install mid-session)
- [ ] Documentation updated
- [ ] Changelog updated

## Success Metrics

After deployment, check:
- No errors in logs
- Banner shows/hides correctly
- Climate type behaves correctly
- Users understand the relationship
- No confusion in issues/discussions

## Next Steps

**After MVP:**
1. Deploy to beta
2. Gather user feedback
3. Monitor usage
4. Decide on Phase 2 (profile builder)

**Phase 2 (if needed):**
- SmartIR profile builder UI
- Guided command learning
- JSON file generation
- YAML config generation

## Resources

- **Design**: `docs/SMARTIR_SOFT_INTEGRATION.md`
- **Implementation**: `docs/SMARTIR_IMPLEMENTATION_PLAN.md`
- **Summary**: `SMARTIR_INTEGRATION_SUMMARY.md`
- **SmartIR GitHub**: https://github.com/smartHomeHub/SmartIR

## Questions?

- **Why soft integration?** - Don't force dependencies
- **Why not hard dependency?** - Not everyone needs climate
- **Why auto-detect?** - Better UX, no config needed
- **Why Phase 2?** - Wait for user feedback first

## Estimated Time

- Backend: 30 minutes
- Frontend service: 30 minutes  
- Banner: 30 minutes
- Entity hints: 30 minutes
- Testing: 1 hour
- **Total: 3 hours**

## Ready to Start?

1. Read `SMARTIR_IMPLEMENTATION_PLAN.md` for detailed steps
2. Start with backend integration
3. Test each piece as you go
4. Deploy when all tests pass

Good luck! 🚀
