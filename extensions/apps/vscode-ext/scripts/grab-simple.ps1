# Simple method: grab text from currently focused field with better Cursor AI support
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient

# Function to send keys
$shell = New-Object -ComObject WScript.Shell

# Check if we're in a Cursor window and try to focus on likely input area
try {
    # Get foreground window title
    Add-Type -TypeDefinition @"
        using System;
        using System.Runtime.InteropServices;
        using System.Text;
        public class WindowHelper {
            [DllImport("user32.dll")]
            public static extern IntPtr GetForegroundWindow();
            [DllImport("user32.dll")]
            public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
        }
"@
    
    $hwnd = [WindowHelper]::GetForegroundWindow()
    $title = New-Object System.Text.StringBuilder 256
    [WindowHelper]::GetWindowText($hwnd, $title, 256) | Out-Null
    $windowTitle = $title.ToString()
    
    # If we're in Cursor, try to click in the likely input area (bottom of window)
    if ($windowTitle -match "(?i)cursor") {
        # Get window bounds and click in bottom area where input usually is
        $elem = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
        if ($null -ne $elem) {
            $rect = $elem.Current.BoundingRectangle
            # Click in bottom 20% of window, center horizontally
            $clickX = $rect.X + ($rect.Width / 2)
            $clickY = $rect.Y + ($rect.Height * 0.85)
            
            # Move mouse and click
            [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($clickX, $clickY)
            Start-Sleep -Milliseconds 50
            
            # Simulate mouse click
            Add-Type -TypeDefinition @"
                using System;
                using System.Runtime.InteropServices;
                public class MouseHelper {
                    [DllImport("user32.dll")]
                    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, IntPtr dwExtraInfo);
                    public const uint MOUSEEVENTF_LEFTDOWN = 0x02;
                    public const uint MOUSEEVENTF_LEFTUP = 0x04;
                }
"@
            [MouseHelper]::mouse_event(0x02, 0, 0, 0, [IntPtr]::Zero) # Mouse down
            Start-Sleep -Milliseconds 10
            [MouseHelper]::mouse_event(0x04, 0, 0, 0, [IntPtr]::Zero) # Mouse up
            Start-Sleep -Milliseconds 100
        }
    }
} catch {
    # If focus detection fails, continue with normal method
}

# Save current clipboard content
$originalClipboard = ""
try {
    $originalClipboard = [System.Windows.Forms.Clipboard]::GetText()
} catch {}

# Clear clipboard first
try {
    [System.Windows.Forms.Clipboard]::Clear()
    Start-Sleep -Milliseconds 100
} catch {}

# Try to select all text in currently focused field
$shell.SendKeys('^a')
Start-Sleep -Milliseconds 200

# Copy selected text
$shell.SendKeys('^c')
Start-Sleep -Milliseconds 300

# Read from clipboard
$capturedText = ""
try {
    $capturedText = [System.Windows.Forms.Clipboard]::GetText()
} catch {}

# Restore original clipboard content
try {
    if ($originalClipboard -and $originalClipboard.Length -gt 0) {
        [System.Windows.Forms.Clipboard]::SetText($originalClipboard)
    } else {
        [System.Windows.Forms.Clipboard]::Clear()
    }
} catch {}

# Check if we got meaningful text (not just whitespace or very short)
if ($capturedText -and $capturedText.Trim().Length -gt 0) {
    # Filter out single character or very short accidental captures
    if ($capturedText.Trim().Length -ge 2) {
        # Normalize line endings
        $normalized = ($capturedText -replace "\r\n?", "`n")
        Write-Output $normalized
    } else {
        exit 2
    }
} else {
    exit 2
}