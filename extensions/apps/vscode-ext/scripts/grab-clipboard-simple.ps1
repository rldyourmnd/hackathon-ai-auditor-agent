# Simple clipboard grab - just read current clipboard content
$ErrorActionPreference = 'Stop'

# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Windows.Forms

# Get current clipboard content without any keyboard actions
$clipboardText = ""
try {
    $clipboardText = [System.Windows.Forms.Clipboard]::GetText()
} catch {
    exit 1
}

# Check if we got meaningful text
if ($clipboardText -and $clipboardText.Trim().Length -gt 0) {
    # Normalize line endings and ensure proper UTF-8 encoding
    $normalized = ($clipboardText -replace "\r\n?", "`n")
    
    # Output with proper UTF-8 encoding to avoid character corruption
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $bytes = $utf8NoBom.GetBytes($normalized)
    [Console]::OpenStandardOutput().Write($bytes, 0, $bytes.Length)
} else {
    exit 2
}