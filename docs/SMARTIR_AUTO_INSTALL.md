# SmartIR Automated Installation - Design Document

## Overview
This document explores the feasibility of automating SmartIR installation from within Broadlink Manager.

---

## Current Manual Installation Process

### Steps Required
1. **Download SmartIR**
   - Clone or download from https://github.com/smartHomeHub/SmartIR
   - Extract to `/config/custom_components/smartir/`

2. **Update configuration.yaml**
   - Add `smartir:` to configuration.yaml

3. **Restart Home Assistant**
   - Required for HA to load the custom component

---

## Automated Installation - Feasibility

### ✅ What We CAN Do

#### 1. Download and Extract Files
```python
# Backend endpoint: POST /api/smartir/install
async def install_smartir():
    """Download and install SmartIR custom component"""
    
    # 1. Download latest release from GitHub
    url = "https://github.com/smartHomeHub/SmartIR/archive/refs/heads/master.zip"
    response = requests.get(url)
    
    # 2. Extract to /config/custom_components/smartir/
    import zipfile
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        # Extract only the smartir directory
        for member in zip_file.namelist():
            if member.startswith('SmartIR-master/custom_components/smartir/'):
                # Extract to /config/custom_components/smartir/
                target_path = member.replace('SmartIR-master/custom_components/', '')
                zip_file.extract(member, '/config/custom_components/')
    
    return {"success": True, "message": "SmartIR files installed"}
```

#### 2. Modify configuration.yaml
```python
# Add smartir: to configuration.yaml
config_path = Path("/config/configuration.yaml")

# Read existing config
with open(config_path, 'r') as f:
    config_content = f.read()

# Check if smartir already exists
if 'smartir:' not in config_content:
    # Append smartir configuration
    with open(config_path, 'a') as f:
        f.write('\n# SmartIR Integration\nsmartir:\n')
    
    return {"success": True, "config_updated": True}
```

#### 3. Detect Installation Status
```python
# Already implemented in smartir_detector.py
def is_installed():
    """Check if SmartIR is installed"""
    smartir_path = Path("/config/custom_components/smartir")
    return smartir_path.exists() and (smartir_path / "__init__.py").exists()
```

---

### ❌ What We CANNOT Do

#### 1. Restart Home Assistant
- **Problem**: Add-ons cannot restart Home Assistant
- **Reason**: Security restriction - add-ons run in isolated containers
- **Workaround**: User must manually restart HA

#### 2. Verify Installation Success
- **Problem**: Cannot verify SmartIR loaded correctly until HA restarts
- **Reason**: Custom components only load on HA startup
- **Workaround**: Show instructions to restart and verify

---

## Proposed Implementation

### Option 1: Full Automation (Recommended)
**Install files + config, user restarts HA**

**Pros:**
- ✅ One-click installation
- ✅ Reduces manual steps from 3 to 1
- ✅ Less error-prone
- ✅ Better UX

**Cons:**
- ❌ Still requires manual HA restart
- ❌ Risk of modifying configuration.yaml incorrectly
- ❌ Could break HA if YAML syntax error

**Implementation:**
```javascript
// Frontend: Install button click
async function installSmartIR() {
  if (!confirm('This will download SmartIR and modify your configuration.yaml. Continue?')) {
    return
  }
  
  try {
    const response = await fetch('/api/smartir/install', { method: 'POST' })
    const result = await response.json()
    
    if (result.success) {
      showModal({
        title: 'SmartIR Installed Successfully!',
        message: `
          SmartIR has been installed to /config/custom_components/smartir/
          
          Next Steps:
          1. Go to Settings → System → Restart Home Assistant
          2. Wait for restart to complete
          3. Return to Broadlink Manager to verify installation
        `,
        actions: [
          { label: 'Go to Settings', action: () => window.location.href = '/config/server_control' },
          { label: 'Close', action: () => {} }
        ]
      })
    }
  } catch (err) {
    showError('Installation failed: ' + err.message)
  }
}
```

---

### Option 2: Manual with Guidance (Current)
**Show installation guide, user does everything**

**Pros:**
- ✅ No risk of breaking HA
- ✅ User has full control
- ✅ Follows HA best practices

**Cons:**
- ❌ More steps for user
- ❌ Higher chance of errors
- ❌ Less convenient

**Current Implementation:**
- "Install SmartIR" button → Opens installation guide modal
- "View on GitHub" button → Opens SmartIR repo
- "Documentation" button → Opens SmartIR README

---

## Recommendation

### Hybrid Approach: Automated with Safety Checks

**Phase 1: Guided Installation (Current)**
- Keep current manual approach
- Improve installation guide modal
- Add step-by-step instructions with screenshots

**Phase 2: Semi-Automated (Future)**
- Add "Auto-Install" button (advanced users)
- Perform safety checks before installation:
  - ✅ Check if custom_components directory exists
  - ✅ Backup configuration.yaml before modifying
  - ✅ Validate YAML syntax after modification
  - ✅ Rollback if validation fails
- Show clear instructions for HA restart
- Add verification step after restart

**Phase 3: Full Automation (Future)**
- Integrate with Home Assistant Supervisor API (if available)
- Trigger HA restart programmatically (if possible)
- Auto-verify installation after restart

---

## Safety Considerations

### 1. Backup Before Modification
```python
# Always backup configuration.yaml
import shutil
from datetime import datetime

backup_path = f"/config/configuration.yaml.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2("/config/configuration.yaml", backup_path)
```

### 2. YAML Validation
```python
import yaml

def validate_yaml(file_path):
    """Validate YAML syntax"""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        return False, str(e)
```

### 3. Rollback on Failure
```python
def rollback_installation():
    """Rollback installation if something fails"""
    # Remove SmartIR files
    shutil.rmtree("/config/custom_components/smartir", ignore_errors=True)
    
    # Restore configuration.yaml from backup
    if backup_path.exists():
        shutil.copy2(backup_path, "/config/configuration.yaml")
```

---

## User Experience Flow

### Automated Installation Flow
```
1. User clicks "Install SmartIR"
   ↓
2. Show confirmation dialog with warnings
   ↓
3. Backend downloads and installs files
   ↓
4. Backend backs up configuration.yaml
   ↓
5. Backend adds smartir: to configuration.yaml
   ↓
6. Backend validates YAML syntax
   ↓
7. Show success modal with restart instructions
   ↓
8. User restarts Home Assistant
   ↓
9. User returns to Broadlink Manager
   ↓
10. SmartIR detected and ready to use
```

---

## Implementation Checklist

### Backend (Python)
- [ ] Create `/api/smartir/install` endpoint
- [ ] Implement GitHub download and extraction
- [ ] Implement configuration.yaml modification
- [ ] Add YAML validation
- [ ] Add backup/rollback mechanism
- [ ] Add error handling and logging

### Frontend (Vue)
- [ ] Update "Install SmartIR" button handler
- [ ] Create installation confirmation dialog
- [ ] Create success modal with restart instructions
- [ ] Add progress indicator during installation
- [ ] Add error handling and user feedback

### Testing
- [ ] Test on fresh HA installation
- [ ] Test with existing SmartIR installation
- [ ] Test YAML validation
- [ ] Test rollback on failure
- [ ] Test with various HA configurations

---

## Conclusion

**Current Decision: Keep Manual Installation**
- Safer and follows HA best practices
- Less risk of breaking user's HA instance
- User has full control and understanding

**Future Enhancement: Add Optional Auto-Install**
- Implement as advanced feature with clear warnings
- Require explicit user confirmation
- Include comprehensive safety checks
- Provide clear rollback instructions

---

## Related Files
- `app/smartir_detector.py` - SmartIR detection logic
- `frontend/src/components/smartir/SmartIRStatusCard.vue` - Installation UI
- `frontend/src/views/Dashboard.vue` - Installation guide handler

---

**Status**: Design document - not yet implemented  
**Priority**: Low - manual installation works fine  
**Complexity**: Medium - requires careful YAML handling  
**Risk**: Medium-High - could break HA if not done carefully
