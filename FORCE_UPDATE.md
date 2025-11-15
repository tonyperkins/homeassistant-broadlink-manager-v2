# Force Alpha 16 Update on Supervisor

Supervisor caches repository metadata. To force it to see alpha.16 immediately:

## Method 1: Remove and Re-add Repository (Fastest)

```bash
# Remove repository
ha store repositories remove https://github.com/tonyperkins/homeassistant-broadlink-manager-v2

# Wait a moment
sleep 5

# Re-add repository
ha store repositories add https://github.com/tonyperkins/homeassistant-broadlink-manager-v2

# Wait for it to load
sleep 10

# Check version
ha addons info 1ed199ed_broadlink-manager-v2 | grep version
```

## Method 2: Restart Supervisor

```bash
ha supervisor restart
sleep 60
ha addons reload
ha addons info 1ed199ed_broadlink-manager-v2 | grep version
```

## Method 3: Wait

Supervisor's cache expires after ~24 hours. Alpha 16 will appear automatically.

## After Update Appears

```bash
# Update to alpha 16
ha addons update 1ed199ed_broadlink-manager-v2

# Start the add-on
ha addons start 1ed199ed_broadlink-manager-v2

# Verify it's working
docker logs addon_1ed199ed_broadlink-manager-v2 2>&1 | tail -20
```

## Expected Result

```
version: 0.3.0-alpha.16
version_latest: 0.3.0-alpha.16
update_available: false
```

And logs should show:
```
Starting web server on port 8099
Using Waitress WSGI server
Serving on http://0.0.0.0:8099
```

No "Permission denied" errors!
