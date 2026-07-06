/**
 * Copy text to clipboard with fallback for non-secure contexts (HTTP)
 * and iframe environments (Home Assistant Ingress) where navigator.clipboard
 * may be unavailable or blocked.
 *
 * @param {string} text - The text to copy
 * @returns {Promise<boolean>} - True if copy succeeded
 */
export async function copyToClipboard(text) {
  // Try modern Clipboard API first
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (err) {
      console.warn('navigator.clipboard.writeText failed, falling back:', err)
    }
  }

  // Fallback: use temporary textarea + execCommand('copy')
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-999999px'
  textArea.style.top = '-999999px'
  textArea.setAttribute('readonly', '')
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()

  let successful = false
  try {
    successful = document.execCommand('copy')
    if (!successful) {
      console.warn('execCommand("copy") returned false')
    }
  } catch (err) {
    console.error('execCommand("copy") failed:', err)
  } finally {
    document.body.removeChild(textArea)
  }

  return successful
}

/**
 * Trigger a file download with fallback for mobile/iframe environments.
 * Tries <a download> click first, then window.open as fallback.
 *
 * @param {Blob|string} content - Blob or string content to download
 * @param {string} filename - Download filename
 * @param {string} mimeType - MIME type (default: application/json)
 * @returns {Promise<boolean>} - True if download was triggered
 */
export async function downloadFile(content, filename, mimeType = 'application/json') {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType })
  const url = window.URL.createObjectURL(blob)

  try {
    // Method 1: <a download> click (standard approach)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // Give browser a moment, then try fallback if needed
    await new Promise(resolve => setTimeout(resolve, 300))

    // Method 2: If still here (some mobile browsers need this), try window.open
    // We can't reliably detect if the download started, so we only try this
    // if the first method likely failed (no reliable detection, so we skip
    // to avoid opening duplicate windows on desktop where it worked)
    return true
  } catch (err) {
    console.error('Download failed:', err)
    // Last resort: open in new tab
    window.open(url, '_blank')
    return false
  } finally {
    // Delay revoking to allow download to start
    setTimeout(() => window.URL.revokeObjectURL(url), 1000)
  }
}
