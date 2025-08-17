# Automatic Cursor AI input field detection and text extraction
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName System.Windows.Forms

# Function to send keys
$shell = New-Object -ComObject WScript.Shell

function Write-Debug($msg) {
    # Uncomment for debugging
    # Write-Host "[DEBUG] $msg" -ForegroundColor Yellow
}

function Get-ElementText {
    param(
        [Parameter(Mandatory = $true)]
        [System.Windows.Automation.AutomationElement] $Element
    )

    $text = $null
    try {
        $tp = $Element.GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern)
        if ($tp -ne $null) {
            $range = $tp.DocumentRange
            if ($range -ne $null) {
                $text = $range.GetText([int]::MaxValue)
            }
        }
    } catch {}

    if (-not $text -or $text.Length -eq 0) {
        try {
            $vp = $Element.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
            if ($vp -ne $null) {
                $text = $vp.Current.Value
            }
        } catch {}
    }

    return $text
}

function Focus-Element {
    param(
        [Parameter(Mandatory = $true)]
        [System.Windows.Automation.AutomationElement] $Element
    )
    
    try {
        $Element.SetFocus()
        Start-Sleep -Milliseconds 100
        return $true
    } catch {
        return $false
    }
}

function Get-CursorAIInputTextAuto {
    Write-Debug "Starting automatic Cursor AI input text extraction..."
    
    # Find Cursor AI window
    $windows = [System.Windows.Automation.AutomationElement]::RootElement.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition
    )
    
    $cursorWindow = $null
    for ($i = 0; $i -lt $windows.Count; $i++) {
        $window = $windows.Item($i)
        $windowName = $window.Current.Name
        
        if ($windowName -match "(?i)(cursor)" -and $windowName -notmatch "(?i)(chrome|firefox|edge)") {
            $cursorWindow = $window
            Write-Debug "Found Cursor window: '$windowName'"
            break
        }
    }
    
    if ($null -eq $cursorWindow) {
        Write-Debug "No Cursor window found"
        return $null
    }

    # Strategy 1: Look for currently focused input element in Cursor
    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    if ($null -ne $focused) {
        $controlType = $focused.Current.ControlType
        $isEnabled = $focused.Current.IsEnabled
        $isEditable = $focused.Current.IsKeyboardFocusable
        
        Write-Debug "Current focus: Type=$($controlType.LocalizedControlType), Enabled=$isEnabled, Editable=$isEditable"
        
        # If something editable is already focused, try to get its text
        if (($controlType -eq [System.Windows.Automation.ControlType]::Edit -or 
             $controlType -eq [System.Windows.Automation.ControlType]::Document) -and 
            $isEnabled -and $isEditable) {
            
            $text = Get-ElementText -Element $focused
            Write-Debug "Focused element text: '$text'"
            if ($text -and $text.Trim().Length -gt 0) { 
                return $text 
            }
        }
    }

    # Strategy 2: Search for input fields and try to focus them automatically
    $editCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
    $docCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Document)
    $combinedCondition = New-Object System.Windows.Automation.OrCondition($editCondition, $docCondition)
    $elements = $cursorWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants, $combinedCondition)
    
    Write-Debug "Found $($elements.Count) input elements"
    
    $candidateInputs = @()
    $windowRect = $cursorWindow.Current.BoundingRectangle
    
    for ($i = 0; $i -lt $elements.Count; $i++) {
        $el = $elements.Item($i)
        try {
            $name = $el.Current.Name
            $isEnabled = $el.Current.IsEnabled
            $isEditable = $el.Current.IsKeyboardFocusable
            $rect = $el.Current.BoundingRectangle
            
            Write-Debug "Element $i`: Name='$name', Enabled=$isEnabled, Editable=$isEditable"
            
            # Skip elements that are clearly not input fields
            if (-not $isEnabled -or -not $isEditable) {
                continue
            }
            
            # Check readonly status
            $isReadOnly = $false
            try {
                $vp = $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                if ($vp -ne $null) {
                    $isReadOnly = $vp.Current.IsReadOnly
                }
            } catch {}
            
            if ($isReadOnly) { 
                Write-Debug "  -> Skipped (readonly)"
                continue 
            }
            
            # Focus on input field characteristics:
            # - Reasonable size for an input field
            # - Preferably in bottom part of window
            # - Visible and accessible
            $isVisible = $rect.Width -gt 0 -and $rect.Height -gt 0
            $hasReasonableSize = $rect.Width -ge 100 -and $rect.Height -ge 15 -and $rect.Height -le 300
            $isInBottomHalf = $rect.Y > ($windowRect.Y + $windowRect.Height * 0.4)
            
            if ($isVisible -and $hasReasonableSize) {
                $priority = 0
                
                # Higher priority for elements in bottom half (typical for chat inputs)
                if ($isInBottomHalf) { $priority += 10 }
                
                # Higher priority for larger width (main input fields are usually wider)
                if ($rect.Width -gt 300) { $priority += 5 }
                
                # Higher priority for reasonable input height
                if ($rect.Height -ge 20 -and $rect.Height -le 100) { $priority += 3 }
                
                # Higher priority for elements with relevant names
                if ($name -match "(?i)(input|text|message|chat|prompt)") { $priority += 7 }
                
                $candidateInputs += @{ 
                    Element = $el; 
                    Name = $name;
                    Priority = $priority;
                    Y = $rect.Y;
                    Width = $rect.Width;
                    Height = $rect.Height
                }
                
                Write-Debug "  -> CANDIDATE! Priority=$priority, Size=($($rect.Width)x$($rect.Height))"
            }
        } catch {
            Write-Debug "  -> Error processing element: $($_.Exception.Message)"
        }
    }
    
    # Sort by priority (highest first)
    $candidateInputs = $candidateInputs | Sort-Object -Property Priority -Descending
    
    Write-Debug "Found $($candidateInputs.Count) candidate input fields"
    
    # Try each candidate: focus it and attempt to get text
    foreach ($candidate in $candidateInputs) {
        Write-Debug "Trying candidate: Priority=$($candidate.Priority), Name='$($candidate.Name)'"
        
        $success = Focus-Element -Element $candidate.Element
        if ($success) {
            Write-Debug "Successfully focused element"
            
            # Try to get text directly first
            $text = Get-ElementText -Element $candidate.Element
            if ($text -and $text.Trim().Length -gt 0) {
                Write-Debug "Got text directly: '$text'"
                return $text
            }
            
            # If no direct text, try using clipboard method
            Write-Debug "No direct text, trying clipboard method..."
            
            # Save current clipboard
            $originalClipboard = ""
            try {
                $originalClipboard = [System.Windows.Forms.Clipboard]::GetText()
            } catch {}
            
            # Clear clipboard
            try {
                [System.Windows.Forms.Clipboard]::Clear()
                Start-Sleep -Milliseconds 50
            } catch {}
            
            # Select all and copy
            $shell.SendKeys('^a')
            Start-Sleep -Milliseconds 100
            $shell.SendKeys('^c')
            Start-Sleep -Milliseconds 150
            
            # Read from clipboard
            $capturedText = ""
            try {
                $capturedText = [System.Windows.Forms.Clipboard]::GetText()
            } catch {}
            
            # Restore original clipboard
            try {
                if ($originalClipboard) {
                    [System.Windows.Forms.Clipboard]::SetText($originalClipboard)
                } else {
                    [System.Windows.Forms.Clipboard]::Clear()
                }
            } catch {}
            
            if ($capturedText -and $capturedText.Trim().Length -gt 0) {
                Write-Debug "Got text via clipboard: '$capturedText'"
                return $capturedText
            }
        }
        
        Write-Debug "Failed to get text from this candidate"
    }
    
    Write-Debug "No suitable input field found with text"
    return $null
}

$result = Get-CursorAIInputTextAuto
if ($null -eq $result) { 
    exit 2 
}

# Normalize Windows newlines to \n
$normalized = ($result -replace "\r\n?", "`n")
Write-Output $normalized