# Issue 2: SmartIR Search Analysis

## Status: LIKELY ALREADY FIXED ✅

## Investigation Results

The backend search logic in `app/api/smartir.py` is **correct** and searches all models in the `supportedModels` array:

### Browse Endpoint (`/profiles/browse`)
Lines 1488-1493:
```python
if model:
    model_names = [
        m.lower() for m in model_info.get("models", [])
    ]
    if not any(model.lower() in m for m in model_names):
        continue
```

### Search Endpoint (`/profiles/search`)
Lines 1674-1676:
```python
model_names = model_info.get("models", [])
if any(
    query.lower() in m.lower() for m in model_names
):
```

Both endpoints correctly use `any()` to search **all** models in the array, not just the first one.

## Possible Causes of User's Issue

1. **Stale Index**: User might have an old `smartir_device_index.json` that only indexed the first model
2. **Frontend Caching**: Browser cache showing old results
3. **Case Sensitivity**: Search might be case-sensitive in some places
4. **Typo**: User might have mistyped the model number

## Recommended Actions

1. **Regenerate Index**:
   ```bash
   python scripts/generate_device_index.py
   ```

2. **Clear Browser Cache**: Hard refresh (Ctrl+Shift+R)

3. **Test Search**:
   - Search for "CTXM25RVMA" (exact match)
   - Search for "CTXM25" (partial match)
   - Search for "ctxm25" (lowercase)

4. **Verify Index**:
   Check `smartir_device_index.json` to ensure all models are present:
   ```json
   {
     "code": "5656",
     "models": [
       "CTXM20RVMA",
       "CTXM25RVMA",  ← Should be here
       "CTXM35RVMA",
       ...
     ]
   }
   ```

## If Issue Persists

If the user still can't find "CTXM25RVMA" after regenerating the index:

1. **Check the actual JSON file** at `codes/climate/5656.json` to verify it contains all models
2. **Check frontend filtering** - there might be additional client-side filtering
3. **Check for JavaScript errors** in browser console

## Conclusion

The backend code is correct. The issue is likely:
- Stale index file
- Browser cache
- User error (typo, wrong platform, etc.)

**No code changes needed** - just regenerate the index and clear cache.
