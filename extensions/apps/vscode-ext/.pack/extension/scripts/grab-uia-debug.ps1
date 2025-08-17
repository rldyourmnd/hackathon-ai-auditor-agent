# Debug version of grab-uia.ps1 for troubleshooting Cursor AI text capture
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false

Add-Type -AssemblyName UIAutomationClient

function Write-Debug($msg) {
    Write-Host "[DEBUG] $msg" -ForegroundColor Yellow
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

function Get-CursorAIInputTextDebug {
    Write-Debug "Starting Cursor AI input text search..."
    
    # Find all windows
    $windows = [System.Windows.Automation.AutomationElement]::RootElement.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition
    )
    
    Write-Debug "Found $($windows.Count) windows"
    
    $cursorWindow = $null
    for ($i = 0; $i -lt $windows.Count; $i++) {
        $window = $windows.Item($i)
        $windowName = $window.Current.Name
        Write-Debug "Window $i`: '$windowName'"
        
        if ($windowName -match "(?i)(cursor)" -and $windowName -notmatch "(?i)(chrome|firefox|edge)") {
            $cursorWindow = $window
            Write-Debug "Found Cursor window: '$windowName'"
            break
        }
    }
    
    if ($null -eq $cursorWindow) {
        Write-Debug "No Cursor window found, using focused window"
        $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
        if ($null -eq $focused) { 
            Write-Debug "No focused element found"
            return $null 
        }
        
        $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
        $cursorWindow = $focused
        while ($true) {
            $parent = $walker.GetParent($cursorWindow)
            if ($null -eq $parent) { break }
            $cursorWindow = $parent
            if ($cursorWindow.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window) { break }
        }
        Write-Debug "Using window: '$($cursorWindow.Current.Name)'"
    }

    # Check focused element first
    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    if ($null -ne $focused) {
        $controlType = $focused.Current.ControlType
        $isEnabled = $focused.Current.IsEnabled
        $isEditable = $focused.Current.IsKeyboardFocusable
        
        Write-Debug "Focused element: Type=$($controlType.LocalizedControlType), Enabled=$isEnabled, Editable=$isEditable, Name='$($focused.Current.Name)'"
        
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

    # Find all Edit and Document controls in the window
    $editCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
    $docCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Document)
    $combinedCondition = New-Object System.Windows.Automation.OrCondition($editCondition, $docCondition)
    $editElements = $cursorWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants, $combinedCondition)
    
    Write-Debug "Found $($editElements.Count) Edit/Document controls"
    
    $candidateInputs = @()
    $windowRect = $cursorWindow.Current.BoundingRectangle
    
    for ($i = 0; $i -lt $editElements.Count; $i++) {
        $el = $editElements.Item($i)
        try {
            $name = $el.Current.Name
            $isEnabled = $el.Current.IsEnabled
            $isEditable = $el.Current.IsKeyboardFocusable
            $rect = $el.Current.BoundingRectangle
            
            Write-Debug "Edit control $i`: Name='$name', Enabled=$isEnabled, Editable=$isEditable, Rect=($($rect.X),$($rect.Y),$($rect.Width),$($rect.Height))"
            
            if (-not $isEnabled -or -not $isEditable) {
                Write-Debug "  -> Skipped (not enabled or not editable)"
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
            
            $isInBottomHalf = $rect.Y > ($windowRect.Y + $windowRect.Height * 0.5)
            $hasReasonableWidth = $rect.Width -ge 150
            $isInputHeight = $rect.Height -ge 20 -and $rect.Height -le 200
            $isVisible = $rect.Width -gt 0 -and $rect.Height -gt 0
            
            Write-Debug "  -> BottomHalf=$isInBottomHalf, Width=$hasReasonableWidth, Height=$isInputHeight, Visible=$isVisible"
            
            if ($isInBottomHalf -and $hasReasonableWidth -and $isInputHeight -and $isVisible) {
                $text = Get-ElementText -Element $el
                Write-Debug "  -> CANDIDATE! Text: '$text'"
                $candidateInputs += @{ 
                    Element = $el; 
                    Text = $text; 
                    Name = $name;
                    Y = $rect.Y;
                    Height = $rect.Height
                }
            }
        } catch {
            Write-Debug "  -> Error processing element: $($_.Exception.Message)"
        }
    }
    
    Write-Debug "Found $($candidateInputs.Count) candidate input fields"
    
    # Sort and return best candidate
    $candidateInputs = $candidateInputs | Sort-Object -Property Y -Descending | Sort-Object -Property Height
    
    foreach ($candidate in $candidateInputs) {
        Write-Debug "Checking candidate: Name='$($candidate.Name)', Y=$($candidate.Y), Height=$($candidate.Height), Text='$($candidate.Text)'"
        if ($candidate.Text -and $candidate.Text.Trim().Length -gt 0) {
            Write-Debug "RETURNING TEXT: '$($candidate.Text)'"
            return $candidate.Text
        }
    }
    
    if ($candidateInputs.Count -gt 0) {
        Write-Debug "Found input field but no text, returning empty string"
        return ""
    }

    Write-Debug "No suitable input field found"
    return $null
}

$result = Get-CursorAIInputTextDebug
if ($null -eq $result) { 
    Write-Debug "Script exiting with code 2 (no result)"
    exit 2 
}

Write-Debug "Script returning result: '$result'"
$normalized = ($result -replace "\r\n?", "`n")
Write-Output $normalized