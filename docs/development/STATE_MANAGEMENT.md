# State Management Pattern

## Problem

The app was experiencing recurring issues where UI state didn't match backend state after mutations (create, update, delete operations). This manifested as:

1. **Delete command** - Command appeared deleted but was still in devices.json
2. **Import commands** - Commands imported but UI didn't update until dialog was reopened
3. **Command counts** - Parent component (device list) showed stale counts

## Root Cause

**Optimistic updates without server verification** - The frontend was updating local reactive state immediately without reloading from the server to verify the actual state.

## Solution: Server-First State Management

### Core Principle

**Always reload from server after mutations**

```javascript
// ❌ BAD: Optimistic update
async function deleteCommand(command) {
  await api.delete(`/api/commands/${deviceId}/${command}`)
  // Immediately remove from local state
  commands.value = commands.value.filter(cmd => cmd.name !== command)
}

// ✅ GOOD: Server-first
async function deleteCommand(command) {
  await api.delete(`/api/commands/${deviceId}/${command}`)
  // Reload from server to get actual state
  await loadCommands(true) // forceReload=true
}
```

### Pattern for All Mutations

1. **Perform mutation** (POST, PUT, DELETE)
2. **Force reload from server** with `forceReload=true`
3. **Emit event to parent** to update related state
4. **Show success message** to user

```javascript
async function handleMutation() {
  try {
    // 1. Perform mutation
    await api.post('/api/commands/import', { ... })
    
    // 2. Force reload from server
    await loadLearnedCommands(true)  // ← CRITICAL: forceReload=true
    await loadUntrackedCommands()
    
    // 3. Emit event to parent
    emit('learned', {
      deviceId: props.device.id,
      action: 'imported',
      count: importedCount
    })
    
    // 4. Show success message
    resultMessage.value = 'Success!'
    resultType.value = 'success'
  } catch (error) {
    // On error, still reload to get accurate state
    await loadLearnedCommands(true)
  }
}
```

### Force Reload Implementation

The `loadLearnedCommands(forceReload)` function must:

1. **Always fetch from API when forceReload=true**
2. **Never use cached/prop data when forceReload=true**
3. **Update all reactive state from API response**

```javascript
const loadLearnedCommands = async (forceReload = false) => {
  loadingCommands.value = true
  try {
    if (forceReload && props.device.id) {
      // Force reload from API - ignore props.device.commands
      const response = await api.get(`/api/commands/${props.device.id}`)
      const commands = response.data.commands || {}
      
      learnedCommands.value = Object.entries(commands).map(([name, data]) => ({
        name,
        type: data.type || 'ir'
      }))
    } else if (props.device.commands) {
      // Use cached data from props
      learnedCommands.value = Object.entries(props.device.commands).map(...)
    }
  } finally {
    loadingCommands.value = false
  }
}
```

### Parent-Child Communication

When child components mutate data, they must notify parent to update shared state:

```javascript
// Child: CommandLearner.vue
emit('learned', {
  deviceId: props.device.id,
  action: 'deleted', // or 'imported', 'learned'
  commandName: command,
  count: importedCount
})

// Parent: DeviceList.vue
const handleCommandLearned = async (event) => {
  // Reload all devices to get updated command counts
  await loadDevices()
}
```

## Fixed Issues

### 1. Delete Command
**Before:** Optimistic update removed command from UI but not from devices.json
**After:** Deletes from backend, then reloads from server to show actual state

### 2. Import Commands
**Before:** Called `loadLearnedCommands()` without forceReload, used cached data
**After:** Calls `loadLearnedCommands(true)` to force reload from server

### 3. Command Counts
**Before:** Parent component didn't know about changes
**After:** Child emits event, parent reloads all devices to update counts

## Best Practices

### ✅ DO

- Always pass `forceReload=true` after mutations
- Emit events to parent after mutations
- Reload related data (e.g., untracked commands after import)
- Handle errors by reloading to get accurate state
- Show loading states during reloads

### ❌ DON'T

- Use optimistic updates without server verification
- Assume mutations succeeded without checking
- Forget to emit events to parent
- Cache data across mutations
- Use stale prop data after mutations

## Testing Checklist

After implementing any mutation:

- [ ] Does UI update immediately after mutation?
- [ ] Does UI show correct state if dialog is closed and reopened?
- [ ] Does parent component (device list) show updated counts?
- [ ] Does error handling reload to show accurate state?
- [ ] Are related lists updated (e.g., untracked commands)?

## Future Improvements

Consider implementing:

1. **Centralized state management** (Pinia/Vuex) to avoid prop drilling
2. **Optimistic updates with rollback** for better UX
3. **WebSocket updates** for real-time sync across tabs
4. **Debounced reloads** to avoid excessive API calls

## Related Files

- `frontend/src/components/commands/CommandLearner.vue` - Command management
- `app/api/commands.py` - Command API endpoints
- `app/device_manager.py` - Device state management
