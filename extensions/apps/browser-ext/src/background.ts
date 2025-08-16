// Background service worker for AI Auditor MV3
console.log('AI Auditor background service worker loaded');

// Handle messages between content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message.type);
  
  // Forward analysis results to any listening popups
  if (message.type === 'ANALYSIS_COMPLETED') {
    // This will be received by the popup if it's open
    // The popup already listens for these messages directly
    console.log('Analysis completed for:', message.url);
  }
  
  return false; // Don't keep the message channel open
});

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('AI Auditor extension installed');
    
    // Set default settings
    chrome.storage.local.set({
      settings: {
        offlineMode: true,
        blockOnHighRisk: false,
        provider: 'local',
        model: 'none'
      },
      history: []
    });
  }
});


