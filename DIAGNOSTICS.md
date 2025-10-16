# Diagnostics & Troubleshooting

## Submitting Issues

When submitting an issue on GitHub, please include diagnostic information to help us troubleshoot faster.

### How to Generate Diagnostics

#### **Option 1: Copy Summary (Quick)**
1. Click the **Diagnostics** button in the UI
2. Select **Copy Summary**
3. Paste into your GitHub issue

This provides a quick overview of your system configuration.

#### **Option 2: Download Full Report (Recommended)**
1. Click the **Diagnostics** button in the UI
2. Select **Download Full Report**
3. Attach the ZIP file to your GitHub issue

This includes complete diagnostic information in a sanitized format.

### What's Included

The diagnostic report includes:

#### **System Information**
- Operating system and version
- Python version
- Platform architecture

#### **Configuration**
- Storage path
- Log level
- Home Assistant connectivity status
- **Note:** Tokens and passwords are automatically removed

#### **Device Information**
- Total device count
- Device breakdown by type (Broadlink, SmartIR)
- Entity type distribution
- **Note:** Sensitive command data is removed

#### **Integration Status**
- SmartIR installation status
- Broadlink device detection

#### **Storage Information**
- File existence and sizes
- Last modification times
- Backup file status

#### **Command Structure**
- Command file listing
- Command names and types (IR/RF)
- Command counts per device
- Import/learned status
- **Note:** Actual IR/RF codes are NOT included (privacy)

### Privacy & Security

**All diagnostic data is automatically sanitized:**
- ✅ Tokens are removed
- ✅ Passwords are removed
- ✅ API keys are removed
- ✅ Learned IR/RF codes are removed (only command names included)
- ✅ Only metadata is included

**You can review the data before sharing:**
- The ZIP file contains human-readable JSON and Markdown files
- Open and review before attaching to GitHub issues
- Remove any additional sensitive information if needed

### Manual Diagnostics

If the automatic diagnostics don't work, you can manually collect:

1. **System Info:**
   ```bash
   python --version
   uname -a  # Linux/Mac
   systeminfo  # Windows
   ```

2. **Device Count:**
   - Check `devices.json` in your storage directory
   - Count entries (don't share the full file - it contains IR/RF codes)

3. **Logs:**
   - Last 50-100 lines from the application log
   - Look for ERROR or WARNING messages

4. **Configuration:**
   - Storage path location
   - Installation type (add-on vs standalone)
   - Home Assistant version

### API Endpoints

For advanced users or automation:

#### **GET /api/diagnostics**
Returns diagnostic data as JSON.

```bash
curl http://localhost:8099/api/diagnostics
```

#### **GET /api/diagnostics/markdown**
Returns diagnostic summary as Markdown.

```bash
curl http://localhost:8099/api/diagnostics/markdown
```

#### **GET /api/diagnostics/download**
Downloads diagnostic bundle as ZIP file.

```bash
curl -O http://localhost:8099/api/diagnostics/download
```

### Example Issue Template

```markdown
## Issue Description
[Describe your issue here]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [etc.]

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Diagnostics
[Paste diagnostic summary here or attach ZIP file]

## Additional Context
[Any other relevant information]
```

### Common Issues

#### **Diagnostics Button Not Visible**
- Ensure you're running the latest version
- Check browser console for errors (F12)
- Try refreshing the page

#### **Download Fails**
- Check browser's download settings
- Ensure sufficient disk space
- Try "Copy Summary" instead

#### **Clipboard Copy Fails**
- Some browsers require HTTPS for clipboard access
- Try the "Download Full Report" option instead
- Manually copy from the downloaded files

### Need Help?

- 📖 [Documentation](https://github.com/yourusername/broadlink-manager)
- 🐛 [Report Issues](https://github.com/yourusername/broadlink-manager/issues)
- 💬 [Discussions](https://github.com/yourusername/broadlink-manager/discussions)
