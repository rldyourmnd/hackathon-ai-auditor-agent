// Minimal browser messaging adapter (placeholder)
export function sendMessageToBackground(message: unknown) {
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
    chrome.runtime.sendMessage(message);
  }
}



