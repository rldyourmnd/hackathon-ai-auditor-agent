$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false

Add-Type -AssemblyName UIAutomationClient

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

function Get-CursorAIInputText {
    # Strategy 1: Find active Cursor AI window
    $windows = [System.Windows.Automation.AutomationElement]::RootElement.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition
    )
    
    $cursorWindow = $null
    for ($i = 0; $i -lt $windows.Count; $i++) {
        $window = $windows.Item($i)
        $windowName = $window.Current.Name
        # Look for Cursor-related window titles
        if ($windowName -match "(?i)(cursor)" -and $windowName -notmatch "(?i)(chrome|firefox|edge)") {
            $cursorWindow = $window
            break
        }
    }
    
    # Fallback: use focused window
    if ($null -eq $cursorWindow) {
        $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
        if ($null -eq $focused) { return $null }
        
        $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
        $cursorWindow = $focused
        while ($true) {
            $parent = $walker.GetParent($cursorWindow)
            if ($null -eq $parent) { break }
            $cursorWindow = $parent
            if ($cursorWindow.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window) { break }
        }
    }
    
    if ($null -eq $cursorWindow) { return $null }

    # Strategy 2: Find FOCUSED element first (user is typing in it)
    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    if ($null -ne $focused) {
        # Check if focused element is an edit control and is writable
        $controlType = $focused.Current.ControlType
        $isEnabled = $focused.Current.IsEnabled
        $isEditable = $focused.Current.IsKeyboardFocusable
        
        if (($controlType -eq [System.Windows.Automation.ControlType]::Edit -or 
             $controlType -eq [System.Windows.Automation.ControlType]::Document) -and 
            $isEnabled -and $isEditable) {
            
            $text = Get-ElementText -Element $focused
            if ($text -and $text.Trim().Length -gt 0) { 
                return $text 
            }
        }
    }

    # Strategy 3: Look for INPUT FIELD patterns specifically (not message history)
    $inputPatterns = @(
        'Type to Cursor',
        'Ask Cursor',
        'Type your message',
        'Chat input',
        'Message input',
        'Prompt input',
        'Input',
        'textarea',
        'message composer',
        'text input'
    )
    
    foreach ($pattern in $inputPatterns) {
        # Try exact name match
        $nameCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $pattern)
        $elements = $cursorWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants, $nameCondition)
        for ($i = 0; $i -lt $elements.Count; $i++) {
            $el = $elements.Item($i)
            if ($el.Current.IsEnabled -and $el.Current.IsKeyboardFocusable) {
                $text = Get-ElementText -Element $el
                if ($text -and $text.Trim().Length -gt 0) { return $text }
            }
        }
    }

    # Strategy 4: Find Edit AND Document controls that are ACTIVE INPUT FIELDS (not readonly message history)
    $editCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
    $docCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Document)
    $combinedCondition = New-Object System.Windows.Automation.OrCondition($editCondition, $docCondition)
    $editElements = $cursorWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants, $combinedCondition)
    
    $candidateInputs = @()
    $windowRect = $cursorWindow.Current.BoundingRectangle
    
    for ($i = 0; $i -lt $editElements.Count; $i++) {
        $el = $editElements.Item($i)
        try {
            # IMPORTANT: Only consider EDITABLE fields, not readonly history
            if (-not $el.Current.IsEnabled -or -not $el.Current.IsKeyboardFocusable) {
                continue
            }
            
            # Check if it's NOT readonly (readonly fields usually contain message history)
            $isReadOnly = $false
            try {
                $vp = $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                if ($vp -ne $null) {
                    $isReadOnly = $vp.Current.IsReadOnly
                }
            } catch {}
            
            if ($isReadOnly) { continue }
            
            $rect = $el.Current.BoundingRectangle
            
            # Input field characteristics for active input:
            # - In bottom 50% of window (typical for chat inputs)
            # - Reasonable width (at least 150px)
            # - Not too tall (input fields are usually single/few lines)
            # - Must be visible and enabled
            $isInBottomHalf = $rect.Y > ($windowRect.Y + $windowRect.Height * 0.5)
            $hasReasonableWidth = $rect.Width -ge 150
            $isInputHeight = $rect.Height -ge 20 -and $rect.Height -le 200
            $isVisible = $rect.Width -gt 0 -and $rect.Height -gt 0
            
            if ($isInBottomHalf -and $hasReasonableWidth -and $isInputHeight -and $isVisible) {
                $text = Get-ElementText -Element $el
                $candidateInputs += @{ 
                    Element = $el; 
                    Text = $text; 
                    Area = $rect.Width * $rect.Height;
                    Y = $rect.Y;
                    Height = $rect.Height
                }
            }
        } catch {
            # Skip elements we can't process
        }
    }
    
    # Sort by Y position (bottommost first), then by smaller height (input fields are usually smaller)
    $candidateInputs = $candidateInputs | Sort-Object -Property Y -Descending | Sort-Object -Property Height
    
    # Return text from the best candidate (prefer those with content, but also return empty fields)
    foreach ($candidate in $candidateInputs) {
        if ($candidate.Text -and $candidate.Text.Trim().Length -gt 0) {
            return $candidate.Text
        }
    }
    
    # If no text found but we have input candidates, return empty string to indicate we found the field
    if ($candidateInputs.Count -gt 0) {
        return ""
    }

    return $null
}

$result = Get-CursorAIInputText
if ($null -eq $result) { exit 2 }

# Normalize Windows newlines to \n
$normalized = ($result -replace "\r\n?", "`n")
Write-Output $normalized


