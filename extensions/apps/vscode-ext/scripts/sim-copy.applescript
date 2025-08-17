on run argv
  set action to "copy"
  if (count of argv) > 0 then set action to item 1 of argv
  tell application "System Events"
    if action is equal to "copy" then
      keystroke "a" using {command down}
      keystroke "c" using {command down}
    else if action is equal to "paste" then
      keystroke "v" using {command down}
    else if action is equal to "send" then
      key code 36
    else if action is equal to "pasteAndSend" then
      keystroke "v" using {command down}
      key code 36
    end if
  end tell
end run
