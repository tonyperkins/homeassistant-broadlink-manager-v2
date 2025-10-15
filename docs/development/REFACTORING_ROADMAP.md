# Broadlink Manager - Refactoring Roadmap

## Completed Work ✅

### Phase 1: CSS Extraction (Oct 12, 2025)
- **Status**: ✅ Complete and tested
- **Changes**:
  - Extracted 790 lines of CSS to `app/static/css/styles.css`
  - Updated Flask to serve static files
  - Updated index.html to use external stylesheet
  - Implemented Material Design Icons (MDI) throughout
  - Fixed syntax errors in JavaScript
- **Results**:
  - File size reduced from 3,930 to 3,082 lines (21.6% reduction)
  - Better code organization
  - Browser caching improves performance
  - Native Home Assistant look with MDI icons

## Future Work 📋

### Phase 2: JavaScript Modularization (DEFERRED)

**Goal**: Split ~2,500 lines of JavaScript into 6 logical ES6 modules

**Estimated Time**: 2-3 hours

**Target Structure**:
```
app/static/js/
├── utils.js        ✅ CREATED (logging, alerts, helpers)
├── api.js          ✅ CREATED (API wrapper functions)
├── ui.js           ⏳ TODO (UI rendering functions)
├── commands.js     ⏳ TODO (command operations)
├── devices.js      ⏳ TODO (device management)
└── main.js         ⏳ TODO (initialization & orchestration)
```

**Benefits**:
- Further reduce index.html to ~500 lines
- Easier debugging and maintenance
- Better code reusability
- Clearer separation of concerns
- Easier testing

---

## Phase 2 Implementation Plan

### Step 1: Complete Module Creation

#### 1. ui.js (~600 lines)
**Purpose**: All UI rendering and DOM manipulation

**Functions to Extract**:
- `renderDeviceList()` - Main device list rendering
- `renderCommandGroups()` - Command group rendering
- `renderManagedDevices()` - Managed devices UI
- `updateHeaderStats()` - Header statistics
- `toggleDevice()` - Device expand/collapse
- `toggleGroup()` - Command group expand/collapse
- `saveUIState()` / `loadUIState()` - UI state persistence

**Dependencies**: 
- Import from: `utils.js` (log, showAlert)
- Export to: `main.js`, `devices.js`

---

#### 2. commands.js (~800 lines)
**Purpose**: All command-related operations

**Functions to Extract**:
- `testCommand()` - Test a command
- `relearnCommand()` - Re-learn existing command
- `deleteCommand()` - Delete a command
- `startLearning()` - Learn new command flow
- `addCommandToDevice()` - Add command to managed device
- `deleteDeviceCommand()` - Delete command from managed device
- `relearnDeviceCommand()` - Re-learn managed device command
- `handleCommandButtonClick()` - Command button event handler
- `setupCommandEventListeners()` - Setup command listeners

**Dependencies**:
- Import from: `api.js`, `utils.js`, `ui.js`
- Export to: `main.js`, `devices.js`

---

#### 3. devices.js (~700 lines)
**Purpose**: Device management operations

**Functions to Extract**:
- `createManagedDevice()` - Create new managed device
- `editManagedDevice()` - Edit existing device
- `deleteManagedDevice()` - Delete managed device
- `convertToManagedDevice()` - Convert legacy to managed
- `confirmConvertDevice()` - Confirm conversion
- `showConvertDeviceDialog()` - Show conversion dialog
- `closeConvertDeviceModal()` - Close conversion modal
- `promptDeviceSelection()` - Device selection prompt

**Dependencies**:
- Import from: `api.js`, `utils.js`, `ui.js`
- Export to: `main.js`

---

#### 4. main.js (~400 lines)
**Purpose**: Application initialization and orchestration

**Functions to Extract**:
- `loadLearnedData()` - Main data loading function
- `init()` - Application initialization
- Event listener setup
- Global state management
- DOMContentLoaded handler

**Dependencies**:
- Import from: ALL other modules
- Export: None (entry point)

---

### Step 2: Update index.html

**Changes Needed**:
1. Replace `<script>` with `<script type="module">`
2. Import main.js as entry point
3. Remove all inline JavaScript
4. Keep only minimal inline code if absolutely necessary

**Example**:
```html
<script type="module">
    import { init } from '/static/js/main.js';
    
    // Initialize app when DOM is ready
    document.addEventListener('DOMContentLoaded', init);
</script>
```

---

### Step 3: Handle Global State

**Current Global Variables** (need to be managed):
```javascript
let learnedData = {};
let currentDevice = '';
let deletedCommandsCache = {};
```

**Solution**: Create a state management object in `main.js`:
```javascript
// main.js
export const appState = {
    learnedData: {},
    currentDevice: '',
    deletedCommandsCache: {}
};
```

---

### Step 4: Testing Checklist

After refactoring, test all functionality:

- [ ] Page loads without errors
- [ ] Device list renders correctly
- [ ] Command groups expand/collapse
- [ ] Test command works
- [ ] Learn new command works
- [ ] Re-learn command works
- [ ] Delete command works
- [ ] Create managed device works
- [ ] Edit managed device works
- [ ] Delete managed device works
- [ ] Convert to managed device works
- [ ] Dark mode toggle works
- [ ] All modals open/close correctly
- [ ] API calls work properly
- [ ] Error handling works
- [ ] Logging works
- [ ] Alerts display correctly

---

## Notes for Future Implementation

### Key Challenges

1. **Circular Dependencies**: Some functions call each other
   - Solution: Careful module design and dependency injection

2. **Shared State**: Many functions access global variables
   - Solution: Centralized state management in main.js

3. **Event Handlers**: Many inline event handlers in HTML strings
   - Solution: Event delegation or convert to proper event listeners

4. **Template Literals**: Large HTML strings embedded in JavaScript
   - Solution: Consider template files or keep as-is for simplicity

### Best Practices

- Use ES6 modules (`import`/`export`)
- One module per file
- Clear, single responsibility per module
- Minimize global state
- Use async/await consistently
- Proper error handling in all modules
- JSDoc comments for all exported functions

### Migration Strategy

**Recommended Approach**: Incremental migration
1. Start with `utils.js` and `api.js` (already created)
2. Test thoroughly
3. Add `ui.js` next
4. Test thoroughly
5. Continue with `commands.js`, `devices.js`, `main.js`
6. Final integration testing

**Alternative Approach**: Big bang migration
- Faster but riskier
- Requires extensive testing
- Harder to debug if issues arise

---

## Expected Final Results

### File Structure
```
app/
├── static/
│   ├── css/
│   │   └── styles.css (790 lines)
│   └── js/
│       ├── utils.js (150 lines)
│       ├── api.js (200 lines)
│       ├── ui.js (600 lines)
│       ├── commands.js (800 lines)
│       ├── devices.js (700 lines)
│       └── main.js (400 lines)
├── templates/
│   └── index.html (~500 lines)
└── web_server.py
```

### Metrics
- **Current**: 3,082 lines in index.html
- **Target**: ~500 lines in index.html
- **Reduction**: ~2,500 lines moved to modules (81% reduction)
- **Total Reduction from Original**: 87% (3,930 → 500 lines)

### Benefits
- ✅ Much easier to maintain
- ✅ Better code organization
- ✅ Easier debugging
- ✅ Better IDE support
- ✅ Reusable code
- ✅ Easier testing
- ✅ Faster development

---

## Timeline Estimate

- **Phase 2 Complete**: 2-3 hours
  - Module creation: 1 hour
  - Integration: 30 minutes
  - Testing: 1-1.5 hours

---

## Status

- **Phase 1**: ✅ Complete (Oct 12, 2025)
- **Phase 2**: ⏳ Deferred (Future session)
- **Phase 3**: 📋 Planned - Vue 3 Rewrite (See below)

---

## Phase 3: Vue 3 Rewrite (PLANNED) 🚀

### Overview

**Goal**: Complete rewrite of the frontend using Vue 3 to enable complex features like SmartIR integration while maintaining clean, maintainable code.

**Status**: Planned for future implementation in a separate fork

**Estimated Timeline**: 6-8 weeks

---

### Why Vue 3?

**Technical Reasons:**
- ✅ **Component-based architecture** - Perfect for complex UI like SmartIR builder
- ✅ **Reactive state management** - Easier to manage device/command state
- ✅ **Single File Components** - HTML, CSS, JS in one file
- ✅ **Smaller bundle size** than React
- ✅ **Better performance** than current vanilla JS approach
- ✅ **Composition API** - Clean, reusable code
- ✅ **Template syntax** - Similar to current Jinja2 templates
- ✅ **Excellent documentation** - Easy to learn and maintain

**Practical Reasons:**
- ✅ **Easier migration path** from current HTML/JS
- ✅ **Solo developer friendly** - Less complex than React
- ✅ **Great component libraries** (Vuetify, PrimeVue)
- ✅ **Built-in state management** (Pinia) simpler than Redux
- ✅ **TypeScript support** (optional but recommended)

---

### Implementation Strategy

#### Option 1: Fork & Full Rewrite (RECOMMENDED)

**Approach:**
1. Fork repository as `broadlink-manager-v2`
2. Keep v1 stable for current users
3. Build v2 from scratch with Vue 3
4. Beta test in parallel
5. Merge back when stable

**Benefits:**
- ✅ Clean slate - no legacy code baggage
- ✅ No risk to stable users
- ✅ Freedom to experiment
- ✅ Can take time to get it right
- ✅ Beta testing pool

**Timeline:** 6-8 weeks

**Repository Structure:**
```
broadlink-manager-v2/
├── frontend/              # Vue 3 app
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.js
├── app/                   # Flask backend (API only)
│   ├── api/
│   └── main.py
└── config.yaml           # v2.0.0-beta.1
```

---

### Tech Stack

**Frontend:**
- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite
- **State Management**: Pinia
- **Router**: Vue Router (if multi-page needed)
- **Component Library**: PrimeVue or Vuetify
- **HTTP Client**: Axios or Fetch API
- **Language**: TypeScript (recommended) or JavaScript

**Backend:**
- **Keep Flask** - No changes needed
- **Convert to pure API** - Return JSON only
- **Add CORS support** - For development

**Build & Deploy:**
- Vite builds to static files
- Flask serves built files from `/static`
- Single Docker image deployment

---

### Project Structure

```
broadlink-manager-v2/
├── frontend/
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── assets/
│   │   │   └── styles/
│   │   │       └── main.css
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Alert.vue
│   │   │   │   ├── Modal.vue
│   │   │   │   └── LoadingSpinner.vue
│   │   │   ├── devices/
│   │   │   │   ├── DeviceList.vue
│   │   │   │   ├── DeviceCard.vue
│   │   │   │   ├── DeviceForm.vue
│   │   │   │   └── CommandList.vue
│   │   │   ├── commands/
│   │   │   │   ├── CommandLearner.vue
│   │   │   │   ├── CommandTester.vue
│   │   │   │   └── CommandGroup.vue
│   │   │   └── smartir/
│   │   │       ├── SmartIRBuilder.vue
│   │   │       ├── ClimateBuilder.vue
│   │   │       ├── MediaPlayerBuilder.vue
│   │   │       ├── FanBuilder.vue
│   │   │       └── CommandForm.vue
│   │   ├── stores/
│   │   │   ├── devices.js
│   │   │   ├── commands.js
│   │   │   ├── smartir.js
│   │   │   └── ui.js
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── Devices.vue
│   │   │   ├── Commands.vue
│   │   │   └── SmartIR.vue
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── utils/
│   │   │   ├── helpers.js
│   │   │   └── validators.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── devices.py
│   │   ├── commands.py
│   │   ├── smartir.py
│   │   └── config.py
│   ├── static/              # Built Vue app goes here
│   ├── main.py
│   └── config.py
├── docs/
│   ├── SMARTIR_INTEGRATION_ROADMAP.md
│   └── VUE_MIGRATION_GUIDE.md
├── config.yaml              # v2.0.0-beta.1
├── Dockerfile
└── README.md
```

---

### Component Architecture

#### Example: Device Management

**DeviceList.vue** (Parent Component)
```vue
<template>
  <div class="device-list">
    <div class="header">
      <h2>Devices</h2>
      <button @click="showCreateForm = true">
        <i class="mdi mdi-plus"></i> Add Device
      </button>
    </div>
    
    <div class="devices">
      <DeviceCard
        v-for="device in devices"
        :key="device.id"
        :device="device"
        @edit="editDevice"
        @delete="deleteDevice"
      />
    </div>
    
    <DeviceForm
      v-if="showCreateForm"
      :device="selectedDevice"
      @save="saveDevice"
      @cancel="closeForm"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '@/stores/devices'
import DeviceCard from './DeviceCard.vue'
import DeviceForm from './DeviceForm.vue'

const deviceStore = useDeviceStore()
const devices = ref([])
const showCreateForm = ref(false)
const selectedDevice = ref(null)

onMounted(async () => {
  await deviceStore.loadDevices()
  devices.value = deviceStore.devices
})

const editDevice = (device) => {
  selectedDevice.value = device
  showCreateForm.value = true
}

const deleteDevice = async (deviceId) => {
  await deviceStore.deleteDevice(deviceId)
}

const saveDevice = async (deviceData) => {
  await deviceStore.saveDevice(deviceData)
  closeForm()
}

const closeForm = () => {
  showCreateForm.value = false
  selectedDevice.value = null
}
</script>

<style scoped>
.device-list {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
</style>
```

**DeviceCard.vue** (Child Component)
```vue
<template>
  <div class="device-card">
    <div class="device-header">
      <i :class="`mdi mdi-${deviceIcon}`"></i>
      <h3>{{ device.name }}</h3>
    </div>
    
    <div class="device-info">
      <span class="type">{{ device.entity_type }}</span>
      <span class="commands">{{ device.commands.length }} commands</span>
    </div>
    
    <div class="actions">
      <button @click="$emit('edit', device)">
        <i class="mdi mdi-pencil"></i>
      </button>
      <button @click="confirmDelete">
        <i class="mdi mdi-delete"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  device: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete'])

const deviceIcon = computed(() => {
  const icons = {
    light: 'lightbulb',
    fan: 'fan',
    switch: 'light-switch',
    media_player: 'television',
    cover: 'window-shutter'
  }
  return icons[props.device.entity_type] || 'devices'
})

const confirmDelete = () => {
  if (confirm(`Delete ${props.device.name}?`)) {
    emit('delete', props.device.id)
  }
}
</script>

<style scoped>
.device-card {
  background: var(--ha-card-background);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
</style>
```

---

### State Management (Pinia)

**stores/devices.js**
```javascript
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useDeviceStore = defineStore('devices', {
  state: () => ({
    devices: [],
    loading: false,
    error: null
  }),
  
  getters: {
    deviceById: (state) => (id) => {
      return state.devices.find(d => d.id === id)
    },
    
    devicesByType: (state) => (type) => {
      return state.devices.filter(d => d.entity_type === type)
    }
  },
  
  actions: {
    async loadDevices() {
      this.loading = true
      try {
        const response = await api.get('/api/devices')
        this.devices = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    
    async saveDevice(deviceData) {
      try {
        if (deviceData.id) {
          await api.put(`/api/devices/${deviceData.id}`, deviceData)
        } else {
          await api.post('/api/devices', deviceData)
        }
        await this.loadDevices()
      } catch (error) {
        this.error = error.message
        throw error
      }
    },
    
    async deleteDevice(deviceId) {
      try {
        await api.delete(`/api/devices/${deviceId}`)
        this.devices = this.devices.filter(d => d.id !== deviceId)
      } catch (error) {
        this.error = error.message
        throw error
      }
    }
  }
})
```

**stores/commands.js**
```javascript
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useCommandStore = defineStore('commands', {
  state: () => ({
    learning: false,
    currentCommand: null,
    testingCommand: null
  }),
  
  actions: {
    async learnCommand(deviceId, commandName) {
      this.learning = true
      this.currentCommand = commandName
      
      try {
        const response = await api.post('/api/learn', {
          device_id: deviceId,
          command: commandName
        })
        return response.data
      } catch (error) {
        throw error
      } finally {
        this.learning = false
        this.currentCommand = null
      }
    },
    
    async testCommand(deviceId, commandName) {
      this.testingCommand = commandName
      
      try {
        await api.post('/api/test', {
          device_id: deviceId,
          command: commandName
        })
      } finally {
        this.testingCommand = null
      }
    },
    
    async deleteCommand(deviceId, commandName) {
      await api.delete(`/api/commands/${deviceId}/${commandName}`)
    }
  }
})
```

---

### API Service Layer

**services/api.js**
```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if needed
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
    return Promise.reject(error)
  }
)

export default api
```

---

### Flask Backend Changes

**app/main.py** (Simplified - API only)
```python
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for development

# Serve Vue app
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

# API Routes
@app.route('/api/devices', methods=['GET'])
def get_devices():
    # Return devices as JSON
    return jsonify(devices)

@app.route('/api/devices', methods=['POST'])
def create_device():
    data = request.json
    # Create device
    return jsonify(device), 201

@app.route('/api/learn', methods=['POST'])
def learn_command():
    data = request.json
    # Learn command logic
    return jsonify(result)

# ... more API routes
```

---

### Build & Deployment

**package.json**
```json
{
  "name": "broadlink-manager-frontend",
  "version": "2.0.0-beta.1",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "pinia": "^2.1.0",
    "vue-router": "^4.2.0",
    "axios": "^1.6.0",
    "primevue": "^3.50.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

**vite.config.js**
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    outDir: '../app/static',
    emptyOutDir: true
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8099',
        changeOrigin: true
      }
    }
  }
})
```

**Dockerfile** (Updated)
```dockerfile
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-alpine
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY --from=frontend-builder /app/app/static ./app/static
COPY config.yaml ./

CMD ["python", "app/main.py"]
```

---

### Development Workflow

**Local Development:**
```bash
# Terminal 1: Run Flask backend
cd app
python main.py

# Terminal 2: Run Vue dev server
cd frontend
npm run dev
# Opens at http://localhost:5173
# Proxies API calls to Flask at :8099
```

**Production Build:**
```bash
cd frontend
npm run build
# Builds to ../app/static/

# Flask serves built files
python app/main.py
```

---

### Migration Phases

#### Phase 3.1: Setup & Infrastructure (Week 1)
- [ ] Fork repository as `broadlink-manager-v2`
- [ ] Set up Vue 3 + Vite project
- [ ] Configure build pipeline
- [ ] Set up Pinia state management
- [ ] Create basic Flask API structure
- [ ] Set up development environment

#### Phase 3.2: Core Components (Week 2-3)
- [ ] Device list component
- [ ] Device form component
- [ ] Command learner component
- [ ] Command tester component
- [ ] Modal/dialog components
- [ ] Alert/notification system

#### Phase 3.3: Feature Parity (Week 4-5)
- [ ] All current features working
- [ ] Device management
- [ ] Command learning
- [ ] Command testing
- [ ] Entity generation
- [ ] Area management
- [ ] Settings

#### Phase 3.4: SmartIR Integration (Week 6-7)
- [ ] SmartIR builder UI
- [ ] Climate device builder
- [ ] Media player builder
- [ ] Fan builder
- [ ] JSON generation
- [ ] File writing
- [ ] YAML generation

#### Phase 3.5: Polish & Testing (Week 8)
- [ ] UI/UX improvements
- [ ] Mobile responsiveness
- [ ] Error handling
- [ ] Loading states
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Beta release

---

### Benefits of Vue 3 Rewrite

**For Development:**
- ✅ **Maintainable code** - Component-based architecture
- ✅ **Faster development** - Reusable components
- ✅ **Better testing** - Unit test components
- ✅ **Type safety** - Optional TypeScript
- ✅ **Hot reload** - Instant feedback during development

**For Users:**
- ✅ **Better performance** - Optimized rendering
- ✅ **Smoother UX** - Reactive updates
- ✅ **Mobile friendly** - Responsive design
- ✅ **Faster loading** - Code splitting
- ✅ **Modern UI** - Better component libraries

**For Features:**
- ✅ **SmartIR integration** - Complex UI made easy
- ✅ **Wizards/flows** - Multi-step processes
- ✅ **Real-time updates** - WebSocket support
- ✅ **Advanced forms** - Validation, dynamic fields
- ✅ **Drag & drop** - Reorder commands/devices

---

### Risks & Mitigation

**Risk 1: Learning Curve**
- Mitigation: Vue 3 has excellent documentation
- Mitigation: Similar to current HTML/JS approach
- Mitigation: Large community for support

**Risk 2: Breaking Changes**
- Mitigation: Keep v1 stable in main repo
- Mitigation: Beta test thoroughly before release
- Mitigation: Provide migration guide

**Risk 3: Build Complexity**
- Mitigation: Vite is simple and fast
- Mitigation: Docker handles build process
- Mitigation: Clear documentation

**Risk 4: Bundle Size**
- Mitigation: Vue 3 is small (~30kb gzipped)
- Mitigation: Code splitting reduces initial load
- Mitigation: Tree shaking removes unused code

---

### Success Criteria

**Technical:**
- [ ] All v1 features working in v2
- [ ] No regressions in functionality
- [ ] Build process automated
- [ ] Tests passing
- [ ] Documentation complete

**Performance:**
- [ ] Initial load < 2 seconds
- [ ] Smooth 60fps interactions
- [ ] Bundle size < 500kb
- [ ] API response times unchanged

**User Experience:**
- [ ] Positive beta tester feedback
- [ ] No major bugs reported
- [ ] Feature requests addressed
- [ ] Migration path clear

---

### Timeline Summary

```
Week 1:   Setup & Infrastructure
Week 2-3: Core Components
Week 4-5: Feature Parity
Week 6-7: SmartIR Integration
Week 8:   Polish & Testing

Total: 6-8 weeks for complete rewrite
```

---

### Next Steps

1. **Decision**: Confirm Vue 3 as framework choice
2. **Fork**: Create `broadlink-manager-v2` repository
3. **Setup**: Initialize Vue 3 + Vite project
4. **POC**: Build one feature as proof of concept
5. **Iterate**: Develop incrementally with testing
6. **Beta**: Release to beta testers
7. **Stable**: Release v2.0.0

---

## Status Summary

- **Phase 1 (CSS)**: ✅ Complete (Oct 12, 2025)
- **Phase 2 (JS Modules)**: ⏳ Deferred
- **Phase 3 (Vue 3)**: 📋 Planned (Oct 13, 2025)

---

*Last Updated: Oct 13, 2025*
