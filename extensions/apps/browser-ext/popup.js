// Popup script for AI Auditor extension
console.log('AI Auditor popup loaded');

// DOM elements
const statusEl = document.getElementById('status');
const offlineModeEl = document.getElementById('offlineMode');
const blockOnHighRiskEl = document.getElementById('blockOnHighRisk');
const providerEl = document.getElementById('provider');
const modelEl = document.getElementById('model');
const historyContainer = document.getElementById('history-container');
const clearHistoryBtn = document.getElementById('clearHistory');

// Settings management
class SettingsManager {
  constructor() {
    this.settings = {
      offlineMode: true,
      blockOnHighRisk: false,
      provider: 'local',
      model: 'none'
    };
    this.history = [];
  }

  async load() {
    try {
      // Load settings from chrome.storage.local
      const result = await chrome.storage.local.get(['settings', 'history']);
      if (result.settings) {
        this.settings = { ...this.settings, ...result.settings };
      }
      if (result.history) {
        this.history = result.history;
      }
    } catch (error) {
      console.log('Failed to load settings, using defaults');
    }
  }

  async save() {
    try {
      await chrome.storage.local.set({
        settings: this.settings,
        history: this.history
      });
    } catch (error) {
      console.log('Failed to save settings');
    }
  }

  updateSetting(key, value) {
    this.settings[key] = value;
    this.save();
    this.updateUI();
    
    // Notify content scripts about settings change
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, {
          type: 'SETTINGS_UPDATED',
          settings: this.settings
        }).catch(() => {
          // Ignore errors if content script is not ready
        });
      }
    });
  }

  addToHistory(analysis) {
    const historyItem = {
      timestamp: Date.now(),
      url: analysis.url || 'Unknown',
      findings: analysis.findings || [],
      textLength: analysis.textLength || 0
    };
    
    this.history.unshift(historyItem);
    
    // Keep only last 10 items
    if (this.history.length > 10) {
      this.history = this.history.slice(0, 10);
    }
    
    this.save();
    this.renderHistory();
  }

  clearHistory() {
    this.history = [];
    this.save();
    this.renderHistory();
  }

  updateUI() {
    // Update status
    if (this.settings.offlineMode) {
      statusEl.className = 'status offline';
      statusEl.textContent = '📱 Режим: Offline анализ';
    } else {
      statusEl.className = 'status online';
      statusEl.textContent = '🌐 Режим: Online анализ';
    }

    // Update form elements
    offlineModeEl.checked = this.settings.offlineMode;
    blockOnHighRiskEl.checked = this.settings.blockOnHighRisk;
    providerEl.value = this.settings.provider;
    modelEl.value = this.settings.model;

    // Enable/disable provider and model based on offline mode
    providerEl.disabled = this.settings.offlineMode;
    modelEl.disabled = this.settings.offlineMode;
  }

  renderHistory() {
    if (this.history.length === 0) {
      historyContainer.innerHTML = `
        <div class="no-history">
          История пуста.<br>
          Нажмите кнопку "🔍 Analyze" на любом AI сайте для анализа.
        </div>
      `;
      return;
    }

    const historyHtml = this.history.map(item => {
      const timeStr = new Date(item.timestamp).toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });

      const findingsHtml = item.findings.length > 0 
        ? item.findings.map(finding => 
            `<div class="finding ${finding.severity}">${finding.message}</div>`
          ).join('')
        : '<div class="finding low">✅ Проблем не найдено</div>';

      return `
        <div class="analysis-item">
          <div class="analysis-time">📅 ${timeStr} • 📄 ${item.textLength} символов</div>
          <div class="analysis-result">${findingsHtml}</div>
        </div>
      `;
    }).join('');

    historyContainer.innerHTML = historyHtml;
  }
}

// Initialize settings manager
const settingsManager = new SettingsManager();

// Event listeners
offlineModeEl.addEventListener('change', (e) => {
  settingsManager.updateSetting('offlineMode', e.target.checked);
});

blockOnHighRiskEl.addEventListener('change', (e) => {
  settingsManager.updateSetting('blockOnHighRisk', e.target.checked);
});

providerEl.addEventListener('change', (e) => {
  settingsManager.updateSetting('provider', e.target.value);
});

modelEl.addEventListener('change', (e) => {
  settingsManager.updateSetting('model', e.target.value);
});

clearHistoryBtn.addEventListener('click', () => {
  if (confirm('Очистить всю историю анализа?')) {
    settingsManager.clearHistory();
  }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ANALYSIS_COMPLETED') {
    settingsManager.addToHistory({
      url: message.url,
      findings: message.findings,
      textLength: message.textLength
    });
  }
});

// Load and initialize on popup open
settingsManager.load().then(() => {
  settingsManager.updateUI();
  settingsManager.renderHistory();
});

// Check current tab to show context-aware info
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const currentTab = tabs[0];
  if (currentTab && currentTab.url) {
    const url = new URL(currentTab.url);
    const hostname = url.hostname;
    
    let siteInfo = '';
    if (hostname.includes('chatgpt.com') || hostname.includes('chat.openai.com')) {
      siteInfo = ' • 💬 ChatGPT обнаружен';
    } else if (hostname.includes('claude.ai')) {
      siteInfo = ' • 🤖 Claude обнаружен';
    } else {
      siteInfo = ' • ❓ AI платформа не обнаружена';
    }
    
    statusEl.textContent += siteInfo;
  }
});
