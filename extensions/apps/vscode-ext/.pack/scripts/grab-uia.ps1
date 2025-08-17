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

function Get-FocusedOrDescendantText {
    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    if ($null -eq $focused) { return $null }

    $text = Get-ElementText -Element $focused
    if ($text -and $text.Trim().Length -gt 0) { return $text }

    # Fallback: scan descendants in the same window for Edit/Document controls
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $root = $focused
    # Climb up to the window root
    while ($true) {
        $parent = $walker.GetParent($root)
        if ($null -eq $parent) { break }
        $root = $parent
        if ($root.Current.ControlType -eq [System.Windows.Automation.ControlType]::Window) { break }
    }

    $condEdit = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
    $condDoc  = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Document)
    $orCond = New-Object System.Windows.Automation.OrCondition($condEdit, $condDoc)

    $desc = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $orCond)
    for ($i = 0; $i -lt $desc.Count; $i++) {
        $el = $desc.Item($i)
        $t = Get-ElementText -Element $el
        if ($t -and $t.Trim().Length -gt 0) { return $t }
    }

    return $null
}

$result = Get-FocusedOrDescendantText
if ($null -eq $result) { exit 2 }

# Normalize Windows newlines to \n
$normalized = ($result -replace "\r\n?", "`n")
Write-Output $normalized


