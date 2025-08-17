# Focused grab method specifically for Cursor AI input field
$ErrorActionPreference = 'Stop'

# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient

# Function to send keys
$shell = New-Object -ComObject WScript.Shell

# Helper to find Cursor AI input field using UIA
function Find-CursorInputField {
    param($rootElement)
    
    try {
        # Look for text input fields in the window
        $textCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
        $documentCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Document)
        
        $orCondition = New-Object System.Windows.Automation.OrCondition($textCondition, $documentCondition)
        $editElements = $rootElement.FindAll([System.Windows.Automation.TreeScope]::Descendants, $orCondition)
        
        foreach ($element in $editElements) {
            if ($null -eq $element) { continue }
            
            try {
                # Check if it's enabled and visible
                if (-not $element.Current.IsEnabled -or -not $element.Current.IsOffscreen) {
                    $bounds = $element.Current.BoundingRectangle
                    
                    # Prefer elements in bottom half of window (where chat input usually is)
                    $windowBounds = $rootElement.Current.BoundingRectangle
                    $isInBottomHalf = $bounds.Y -gt ($windowBounds.Y + $windowBounds.Height * 0.5)
                    
                    # Check if it's not readonly and has reasonable size
                    $isNotReadonly = -not $element.Current.IsReadOnly
                    $hasReasonableSize = $bounds.Width -gt 100 -and $bounds.Height -gt 20
                    
                    if ($isInBottomHalf -and $isNotReadonly -and $hasReasonableSize) {
                        return $element
                    }
                }
            } catch {
                continue
            }
        }
        
        # If no bottom half element found, try any writable element
        foreach ($element in $editElements) {
            if ($null -eq $element) { continue }
            
            try {
                if ($element.Current.IsEnabled -and -not $element.Current.IsOffscreen -and -not $element.Current.IsReadOnly) {
                    $bounds = $element.Current.BoundingRectangle
                    if ($bounds.Width -gt 100 -and $bounds.Height -gt 20) {
                        return $element
                    }
                }
            } catch {
                continue
            }
        }
    } catch {
        # If UIA fails, return null
    }
    
    return $null
}

# Get foreground window
Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;
    using System.Text;
    public class WindowHelper {
        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
    }
"@

$hwnd = [WindowHelper]::GetForegroundWindow()
$title = New-Object System.Text.StringBuilder 256
[WindowHelper]::GetWindowText($hwnd, $title, 256) | Out-Null
$windowTitle = $title.ToString()

# Only proceed if we're in a Cursor window
if ($windowTitle -notmatch "(?i)cursor") {
    # Try to find and focus Cursor window
    $processes = Get-Process | Where-Object { $_.ProcessName -match "(?i)cursor" -and $_.MainWindowTitle -ne "" }
    if ($processes) {
        $cursorProcess = $processes[0]
        [WindowHelper]::SetForegroundWindow($cursorProcess.MainWindowHandle) | Out-Null
        Start-Sleep -Milliseconds 200
        $hwnd = $cursorProcess.MainWindowHandle
    } else {
        Write-Error "Cursor AI window not found"
        exit 1
    }
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

# Try to find and focus the input field using UIA
try {
    $rootElement = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
    if ($null -ne $rootElement) {
        $inputField = Find-CursorInputField $rootElement
        
        if ($null -ne $inputField) {
            # Focus on the input field by clicking it
            $bounds = $inputField.Current.BoundingRectangle
            $centerX = $bounds.X + ($bounds.Width / 2)
            $centerY = $bounds.Y + ($bounds.Height / 2)
            
            # Move mouse and click
            [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($centerX, $centerY)
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
            Start-Sleep -Milliseconds 200
        }
    }
} catch {
    # If UIA fails, fall back to clicking in bottom area
    try {
        $elem = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
        if ($null -ne $elem) {
            $rect = $elem.Current.BoundingRectangle
            # Click more towards bottom where chat input is
            $clickX = $rect.X + ($rect.Width / 2)
            $clickY = $rect.Y + ($rect.Height * 0.9)
            
            [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($clickX, $clickY)
            Start-Sleep -Milliseconds 50
            
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
            [MouseHelper]::mouse_event(0x02, 0, 0, 0, [IntPtr]::Zero)
            Start-Sleep -Milliseconds 10
            [MouseHelper]::mouse_event(0x04, 0, 0, 0, [IntPtr]::Zero)
            Start-Sleep -Milliseconds 200
        }
    } catch {}
}

# Select all text in the focused field
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

# Check if we got meaningful text
if ($capturedText -and $capturedText.Trim().Length -gt 1) {
    $normalized = ($capturedText -replace "\r\n?", "`n")
    
    # Output with proper UTF-8 encoding to avoid character corruption
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $bytes = $utf8NoBom.GetBytes($normalized)
    [Console]::OpenStandardOutput().Write($bytes, 0, $bytes.Length)
} else {
    exit 2
}