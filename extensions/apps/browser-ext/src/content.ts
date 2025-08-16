// Content script: simple example to ask background for analysis
const bodyText = document.body ? document.body.innerText : '';
console.log('AI Auditor content script loaded, text length:', bodyText.length);

export const extractedText = bodyText;

// Example: trigger analysis on first load (throttle in real app)
try {
  chrome.runtime.sendMessage({ type: 'ai-auditor/analyze', text: bodyText }, (resp) => {
    if (chrome.runtime.lastError) return;
    if (resp?.ok) {
      console.log('AI Auditor findings:', resp.res?.findings?.length ?? 0);
    }
  });
} catch {}



