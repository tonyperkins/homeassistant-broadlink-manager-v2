# API Compatibility Quick Reference

## TL;DR

✅ **All deployment modes are fully supported**
- Standalone: 100% compatible
- Docker: 100% compatible  
- HA Add-on: 83% compatible (minor limitation)

## Deployment Mode Comparison

| Feature | Standalone | Docker | HA Add-on |
|---------|-----------|--------|-----------|
| Learn Commands | ✅ | ✅ | ✅ |
| Delete Commands | ✅ | ✅ | ✅ |
| Send Commands | ✅ | ✅ | ✅ |
| Area Management | ✅ | ✅ | ✅ |
| Entity Generation | ✅ | ✅ | ✅ |
| Notifications | ✅ | ✅ | ✅ |
| Storage Access | ✅ | ✅ | ✅ |
| **Reload Integration** | ✅ | ✅ | ⚠️ May not work |

## The Only Limitation

**HA Add-on Mode**: The "Reload Broadlink Integration" button may not work due to security restrictions.

**Workaround**: Manually reload from HA UI:
```
Settings → Devices & Services → Broadlink → ⋮ → Reload
```

## Configuration

### Standalone
```bash
HA_URL=http://192.168.1.100:8123
HA_TOKEN=<your-long-lived-token>
```

### Docker
```bash
docker run -e HA_URL=http://homeassistant.local:8123 \
           -e HA_TOKEN=<your-token> \
           -v /path/to/config:/config \
           broadlink-manager
```

### HA Add-on
No configuration needed - automatically configured by Supervisor.

## Testing

Run deployment mode tests:
```bash
pytest tests/unit/test_deployment_modes.py -v
```

All 20 tests pass ✅

## Documentation

- **Full Analysis**: `docs/development/API_COMPATIBILITY_ANALYSIS.md`
- **Detailed Summary**: `DEPLOYMENT_MODE_TESTING_SUMMARY.md`
- **This Guide**: `API_COMPATIBILITY_QUICK_REFERENCE.md`
