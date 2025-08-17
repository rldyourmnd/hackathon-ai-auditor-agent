$ErrorActionPreference = 'Stop'
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('copy','paste','send','pasteAndSend')]
  [string] $Action
)

$shell = New-Object -ComObject WScript.Shell

if ($Action -eq 'copy') {
  $shell.SendKeys('^a')
  Start-Sleep -Milliseconds 10
  $shell.SendKeys('^c')
  Start-Sleep -Milliseconds 60
} elseif ($Action -eq 'paste') {
  $shell.SendKeys('^v')
  Start-Sleep -Milliseconds 60
} elseif ($Action -eq 'send') {
  $shell.SendKeys('{ENTER}')
  Start-Sleep -Milliseconds 40
} elseif ($Action -eq 'pasteAndSend') {
  $shell.SendKeys('^v')
  Start-Sleep -Milliseconds 40
  $shell.SendKeys('{ENTER}')
  Start-Sleep -Milliseconds 40
}


