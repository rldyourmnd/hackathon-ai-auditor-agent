# Simple clipboard grab fallback method with UTF-8 support
$ErrorActionPreference = 'Stop'

# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Function to send keys
$shell = New-Object -ComObject WScript.Shell

# Save current clipboard content
Add-Type -AssemblyName System.Windows.Forms
$originalClipboard = ""
try {
    $originalClipboard = [System.Windows.Forms.Clipboard]::GetText()
} catch {}

# Clear clipboard first
try {
    [System.Windows.Forms.Clipboard]::Clear()
} catch {}

# Send Ctrl+A to select all text in current field
$shell.SendKeys('^a')
Start-Sleep -Milliseconds 50

# Send Ctrl+C to copy selected text
$shell.SendKeys('^c')
Start-Sleep -Milliseconds 100

# Read from clipboard
$capturedText = ""
try {
    $capturedText = [System.Windows.Forms.Clipboard]::GetText()
} catch {}

# Restore original clipboard if we got text
if ($capturedText -and $capturedText.Trim().Length -gt 0) {
    try {
        [System.Windows.Forms.Clipboard]::SetText($originalClipboard)
    } catch {}
    
    # Output the captured text with proper UTF-8 encoding
    $normalized = ($capturedText -replace "\r\n?", "`n")
    
    # Output with proper UTF-8 encoding to avoid character corruption
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $bytes = $utf8NoBom.GetBytes($normalized)
    [Console]::OpenStandardOutput().Write($bytes, 0, $bytes.Length)
} else {
    # Restore clipboard and exit with error
    try {
        [System.Windows.Forms.Clipboard]::SetText($originalClipboard)
    } catch {}
    exit 2
}