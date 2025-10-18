# SmartIR Profile Browser - Phase 1 Implementation

## Overview

The SmartIR Profile Browser transforms the SmartIR Integration section from a simple profile list into a comprehensive browsing and management system for both index profiles (from the aggregator) and custom user profiles.

## Features Implemented

### 1. Backend API Endpoints

#### `/api/smartir/profiles/browse` (GET)
Browse all profiles with advanced filtering and pagination.

**Query Parameters:**
- `platform` - Filter by platform (climate, fan, media_player, light)
- `manufacturer` - Filter by manufacturer name
- `model` - Filter by model name (partial match)
- `source` - Filter by source (all, index, custom)
- `page` - Page number (default: 1)
- `limit` - Results per page (default: 50)
- `sort_by` - Sort order (code, manufacturer, model)

**Response:**
```json
{
  "success": true,
  "platform": "climate",
  "profiles": [
    {
      "code": "1000",
      "manufacturer": "Daikin",
      "model": "FTXS25CVMA",
      "models": ["FTXS25CVMA"],
      "platform": "climate",
      "source": "index",
      "url": "https://...",
      "controller_brand": "Broadlink",
      "command_count": 0,
      "learned_count": 0,
      "is_custom": false
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1234,
    "total_pages": 25
  },
  "filters": {
    "manufacturer": "",
    "model": "",
    "source": "all"
  }
}
```

#### `/api/smartir/profiles/search` (GET)
Search profiles across all platforms by manufacturer or model.

**Query Parameters:**
- `query` - Search term (required)
- `platform` - Platform to search (default: all)
- `source` - Source filter (all, index, custom)
- `limit` - Max results (default: 100)

**Response:**
```json
{
  "success": true,
  "query": "daikin",
  "results": [
    {
      "code": "1000",
      "manufacturer": "Daikin",
      "model": "FTXS25CVMA",
      "models": ["FTXS25CVMA"],
      "platform": "climate",
      "source": "index",
      "match_type": "manufacturer"
    }
  ],
  "count": 42
}
```

### 2. Frontend Components

#### SmartIRProfileBrowser.vue
Main profile browser component with:
- **Platform Tabs**: Quick switch between Climate, Media Player, Fan, Light
- **Search Bar**: Real-time search with debouncing (300ms)
- **Filters**:
  - Manufacturer dropdown (populated from device index)
  - Source toggle (All, Index, Custom)
  - Sort by (Code, Manufacturer, Model)
- **Pagination**: 50 profiles per page with page navigation
- **Responsive Grid**: Auto-adjusts for desktop/tablet/mobile

#### SmartIRProfileBrowserCard.vue
Individual profile card with:
- **Visual Indicators**:
  - Platform icon with color coding
  - Source badge (Index/Custom)
  - Code badge
  - Additional models count
  - Command count (for custom profiles)
- **Conditional Actions**:
  - **Index Profiles**: View, Clone
  - **Custom Profiles**: View, Test, Edit, Delete
- **Hover Effects**: Card elevation and border highlight

### 3. Integration with SmartIRStatusCard

The profile browser replaces the old profile grid in `SmartIRStatusCard.vue`:
- Removed old filter bar and profile grid
- Integrated `SmartIRProfileBrowser` component
- Added event handlers for all browser actions

### 4. Profile Management Features

#### View Profile
- Fetches full profile JSON from backend
- Displays profile details (TODO: implement viewer modal)

#### Clone Profile
- Fetches index profile from aggregator
- Gets next available custom code (10000+)
- Saves as new custom profile with "(Custom)" suffix
- Refreshes browser to show new profile

#### Edit Profile
- Opens SmartIR Profile Builder in edit mode
- Loads existing profile data
- Supports editing custom profiles only

#### Delete Profile
- Shows confirmation dialog
- Deletes profile JSON file
- Removes from YAML configuration
- Refreshes browser

#### Test Profile (Placeholder)
- Placeholder for Phase 3 implementation
- Will allow testing commands via Broadlink device

## Data Model

### Profile Object
```javascript
{
  code: "1000",              // Device code
  manufacturer: "Daikin",    // Manufacturer name
  model: "FTXS25CVMA",       // Primary model
  models: ["FTXS25CVMA"],    // All supported models
  platform: "climate",       // Platform type
  source: "index",           // "index" or "custom"
  url: "https://...",        // URL to JSON (index only)
  controller_brand: "Broadlink",
  command_count: 42,         // Number of commands
  learned_count: 0,          // Number of learned commands
  is_custom: false,          // Boolean flag
  created_date: 1234567890,  // Unix timestamp (custom only)
  modified_date: 1234567890  // Unix timestamp (custom only)
}
```

## Key Design Decisions

### 1. Lazy Loading
- Index profiles are NOT loaded until viewed/cloned
- Only metadata is displayed in browser
- Reduces memory usage and API calls
- Full profile fetched on-demand

### 2. Source Separation
- Clear visual distinction between index and custom profiles
- Index profiles are read-only (clone to customize)
- Custom profiles have full CRUD operations
- Prevents accidental modification of index profiles

### 3. Performance Optimization
- Pagination limits results to 50 per page
- Debounced search (300ms delay)
- Manufacturer list cached from device index
- No GitHub API calls for browsing

### 4. User Experience
- Platform tabs for quick navigation
- Real-time search feedback
- Clear filter indicators
- Responsive design for all screen sizes
- Toast notifications for all actions

## File Structure

```
app/
  api/
    smartir.py                 # Added browse/search endpoints
frontend/
  src/
    components/
      smartir/
        SmartIRProfileBrowser.vue        # NEW - Main browser
        SmartIRProfileBrowserCard.vue    # NEW - Profile card
        SmartIRStatusCard.vue            # MODIFIED - Integration
docs/
  SMARTIR_PROFILE_BROWSER.md   # NEW - This file
```

## Usage

### For Users

1. **Browse Profiles**:
   - Click platform tab (Climate, Media Player, etc.)
   - Use search bar to find manufacturer/model
   - Filter by manufacturer or source
   - Navigate pages if needed

2. **Clone Index Profile**:
   - Find desired profile from index
   - Click "Clone" button
   - Profile saved as custom code (10000+)
   - Edit cloned profile as needed

3. **Manage Custom Profiles**:
   - Filter by "Custom" source
   - View, test, edit, or delete
   - Full control over custom profiles

### For Developers

**Add new filter:**
```javascript
// In SmartIRProfileBrowser.vue
const filters = ref({
  search: '',
  platform: '',
  manufacturer: '',
  newFilter: ''  // Add here
})

// Update API call
const params = new URLSearchParams({
  // ... existing params
  new_filter: filters.value.newFilter
})
```

**Add new action:**
```javascript
// In SmartIRProfileBrowserCard.vue
<button @click="$emit('newAction', profile)">
  <i class="mdi mdi-icon"></i>
</button>

// In SmartIRProfileBrowser.vue
defineEmits(['view', 'clone', 'edit', 'delete', 'test', 'newAction'])

// In SmartIRStatusCard.vue
<SmartIRProfileBrowser
  @newAction="handleNewAction"
/>

function handleNewAction(profile) {
  // Implementation
}
```

## Next Steps (Future Phases)

### Phase 2: Enhanced Cloning
- [ ] Clone with custom name
- [ ] Selective command cloning
- [ ] Merge multiple profiles
- [ ] Batch cloning

### Phase 3: Testing System
- [ ] Profile tester modal
- [ ] Select Broadlink controller
- [ ] Send test commands
- [ ] Visual feedback
- [ ] Test result history

### Phase 4: Export/Submission
- [ ] Export profile as JSON
- [ ] Validate for aggregator
- [ ] Generate submission PR
- [ ] Direct GitHub integration
- [ ] Submission tracking

## Known Limitations

1. **View Profile**: Currently shows toast, needs viewer modal
2. **Test Profile**: Placeholder, needs implementation
3. **No Bulk Operations**: Can only act on one profile at a time
4. **No Profile Comparison**: Can't compare profiles side-by-side
5. **No Import**: Can't import profiles from external sources

## Performance Considerations

- **Index Size**: ~4000+ profiles, pagination essential
- **Search Performance**: Debounced to prevent excessive API calls
- **Memory Usage**: Lazy loading keeps memory footprint low
- **API Calls**: Minimized through caching and pagination

## Testing

### Manual Testing Checklist
- [ ] Browse all platforms
- [ ] Search by manufacturer
- [ ] Search by model
- [ ] Filter by source (all/index/custom)
- [ ] Sort by code/manufacturer/model
- [ ] Pagination navigation
- [ ] Clone index profile
- [ ] Edit custom profile
- [ ] Delete custom profile
- [ ] Responsive design (mobile/tablet/desktop)

### API Testing
```bash
# Browse profiles
curl "http://localhost:8099/api/smartir/profiles/browse?platform=climate&page=1&limit=50"

# Search profiles
curl "http://localhost:8099/api/smartir/profiles/search?query=daikin&platform=climate"

# Get manufacturers
curl "http://localhost:8099/api/smartir/codes/manufacturers?entity_type=climate"
```

## Troubleshooting

### Profiles not loading
- Check SmartIR is installed
- Verify device index exists (`smartir_device_index.json`)
- Check browser console for errors
- Verify API endpoints are accessible

### Clone fails
- Ensure SmartIR is installed
- Check custom codes directory exists
- Verify next code is available (< 20000)
- Check network connectivity to aggregator

### Search not working
- Clear browser cache
- Check search query length (min 1 char)
- Verify platform is selected
- Check API response in network tab

## Contributing

When adding features to the profile browser:
1. Update API endpoints in `app/api/smartir.py`
2. Update frontend components
3. Add tests
4. Update this documentation
5. Add to CHANGELOG.md

## License

This feature is part of Broadlink Manager v2, licensed under MIT.
SmartIR profiles are from the aggregator repository and maintain their original licenses.
