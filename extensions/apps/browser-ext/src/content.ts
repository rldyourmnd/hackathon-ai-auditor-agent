// Content script for AI Auditor: detects AI chat interfaces and adds analysis functionality
console.log('🚀 AI Auditor content script loaded');

// Enhanced logging utility
function logDebug(step: string, data?: any) {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`🔍 [${timestamp}] AI Auditor: ${step}`, data || '');
}

// Site adapters for different AI platforms
interface SiteAdapter {
  name: string;
  detectSite(): boolean;
  getInputElement(): HTMLElement | null;
  getSendButton(): HTMLElement | null;
  getText(): string;
  injectAnalyzeButton(button: HTMLElement): void;
}

class ChatGPTAdapter implements SiteAdapter {
  name = 'ChatGPT';
  
  detectSite(): boolean {
    const isDetected = window.location.hostname.includes('chatgpt.com') || 
                      window.location.hostname.includes('chat.openai.com');
    logDebug(`ChatGPT detection on ${window.location.hostname}`, { detected: isDetected });
    return isDetected;
  }
  
  getInputElement(): HTMLElement | null {
    const selectors = [
      '#prompt-textarea',
      'textarea[data-id]', 
      'div[contenteditable="true"]',
      'textarea[placeholder*="Message"]',
      'main textarea'
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        logDebug(`Found input element with selector: ${selector}`, { 
          tagName: element.tagName, 
          id: element.id, 
          className: element.className 
        });
        return element as HTMLElement;
      }
    }
    
    logDebug('❌ No input element found', { availableElements: selectors });
    return null;
  }
  
  getSendButton(): HTMLElement | null {
    const selectors = [
      '[data-testid="send-button"]',
      'button[aria-label*="Send"]',
      'button[data-testid="fruitjuice-send-button"]',
      'form button[type="submit"]:last-child',
      'button svg[data-icon="send"]',
      'button:has(svg)'
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        const button = element.tagName === 'BUTTON' ? element : element.closest('button');
        if (button) {
          logDebug(`Found send button with selector: ${selector}`, { 
            tagName: button.tagName,
            className: button.className,
            textContent: button.textContent?.substring(0, 50)
          });
          return button as HTMLElement;
        }
      }
    }
    
    logDebug('❌ No send button found', { selectors });
    return null;
  }
  
  getText(): string {
    const input = this.getInputElement();
    if (!input) {
      logDebug('❌ getText: No input element available');
      return '';
    }
    
    let text = '';
    if (input.tagName === 'TEXTAREA') {
      text = (input as HTMLTextAreaElement).value || '';
      logDebug('📝 getText from textarea', { length: text.length, preview: text.substring(0, 100) });
    } else {
      text = input.textContent || input.innerText || '';
      logDebug('📝 getText from contenteditable', { length: text.length, preview: text.substring(0, 100) });
    }
    
    return text;
  }
  
  injectAnalyzeButton(button: HTMLElement): void {
    const sendButton = this.getSendButton();
    if (!sendButton) return;
    
    // Find the container that holds the send button
    const container = sendButton.parentElement;
    if (!container) return;
    
    // Check if button already exists
    if (container.querySelector('#ai-auditor-analyze-btn')) return;
    
    // Style the analyze button to match ChatGPT design
    button.id = 'ai-auditor-analyze-btn';
    button.style.cssText = `
      margin-right: 6px;
      padding: 8px;
      background: transparent;
      color: #8e8ea0;
      border: 1px solid #40414f;
      border-radius: 6px;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    `;
    
    // Insert before send button
    container.insertBefore(button, sendButton);
  }
}

class ClaudeAdapter implements SiteAdapter {
  name = 'Claude';
  
  detectSite(): boolean {
    return window.location.hostname.includes('claude.ai');
  }
  
  getInputElement(): HTMLElement | null {
    return document.querySelector('div[contenteditable="true"]') ||
           document.querySelector('[data-testid="chat-input"]');
  }
  
  getSendButton(): HTMLElement | null {
    return document.querySelector('[aria-label*="Send"]') ||
           document.querySelector('button[data-testid="send-button"]');
  }
  
  getText(): string {
    const input = this.getInputElement();
    return input ? input.textContent || input.innerText || '' : '';
  }
  
  injectAnalyzeButton(button: HTMLElement): void {
    const sendButton = this.getSendButton();
    if (sendButton && sendButton.parentElement) {
      sendButton.parentElement.insertBefore(button, sendButton);
    }
  }
}

// Available site adapters
const adapters: SiteAdapter[] = [
  new ChatGPTAdapter(),
  new ClaudeAdapter()
];

// Current active adapter
let currentAdapter: SiteAdapter | null = null;

// Detect current site and set adapter
function detectSite(): void {
  logDebug('🌐 Starting site detection', { 
    url: window.location.href,
    hostname: window.location.hostname 
  });
  
  for (const adapter of adapters) {
    if (adapter.detectSite()) {
      currentAdapter = adapter;
      logDebug(`✅ Site detected: ${adapter.name}`);
      initializeForSite();
      return;
    }
  }
  
  logDebug('❌ No supported site detected', { 
    availableAdapters: adapters.map(a => a.name) 
  });
}

// Simple local detectors (inline for browser extension)
interface Finding {
  type: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
  suggestion?: string;
}

function analyzeText(text: string): Finding[] {
  logDebug('🔍 Starting text analysis', { 
    textLength: text.length, 
    textPreview: text.substring(0, 200) + (text.length > 200 ? '...' : '')
  });
  const findings: Finding[] = [];
  
  // Length detector
  logDebug('📏 Checking length', { length: text.length, threshold: 4000 });
  if (text.length > 4000) {
    const finding = {
      type: 'length',
      message: `Очень длинный prompt (${text.length} символов)`,
      severity: 'medium' as const,
      suggestion: 'Рассмотрите разбиение на части'
    };
    findings.push(finding);
    logDebug('⚠️ Length violation detected', finding);
  } else {
    logDebug('✅ Length check passed');
  }
  
  // PII detector (simple patterns)
  logDebug('📧 Checking for email patterns');
  const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
  const emailMatches = text.match(emailPattern);
  logDebug('📧 Email check result', { 
    pattern: emailPattern.toString(),
    matches: emailMatches,
    found: !!emailMatches
  });
  
  if (emailMatches && emailMatches.length > 0) {
    const finding = {
      type: 'pii',
      message: `Обнаружен email адрес: ${emailMatches[0]}`,
      severity: 'high' as const,
      suggestion: 'Удалите персональные данные'
    };
    findings.push(finding);
    logDebug('🚨 Email PII detected', finding);
  } else {
    logDebug('✅ No email found');
  }
  
  logDebug('📱 Checking for phone patterns');
  const phonePattern = /(\+7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}/g;
  const phoneMatches = text.match(phonePattern);
  logDebug('📱 Phone check result', { 
    pattern: phonePattern.toString(),
    matches: phoneMatches,
    found: !!phoneMatches
  });
  
  if (phoneMatches && phoneMatches.length > 0) {
    const finding = {
      type: 'pii', 
      message: `Обнаружен номер телефона: ${phoneMatches[0]}`,
      severity: 'high' as const,
      suggestion: 'Удалите персональные данные'
    };
    findings.push(finding);
    logDebug('🚨 Phone PII detected', finding);
  } else {
    logDebug('✅ No phone found');
  }
  
  // Secret patterns
  logDebug('🔐 Checking for secret patterns');
  const secretPatterns = [
    { name: 'API key pattern', regex: /(?:api[_\-]?key|token|secret)["\s]*[:=]["\s]*[a-zA-Z0-9]{16,}/gi },
    { name: 'OpenAI key pattern', regex: /sk-[a-zA-Z0-9]{48}/g }
  ];
  
  for (const { name, regex } of secretPatterns) {
    const matches = text.match(regex);
    logDebug(`🔐 ${name} check`, { 
      pattern: regex.toString(),
      matches: matches,
      found: !!matches
    });
    
    if (matches && matches.length > 0) {
      const finding = {
        type: 'secret',
        message: `Возможно обнаружен API ключ или токен: ${matches[0].substring(0, 20)}...`,
        severity: 'high' as const,
        suggestion: 'Никогда не передавайте секретные ключи'
      };
      findings.push(finding);
      logDebug('🚨 Secret pattern detected', finding);
      break; // Stop after first match
    }
  }
  
  // Test patterns - добавим для тестирования
  logDebug('🧪 Testing simple patterns');
  if (text.toLowerCase().includes('test@example.com')) {
    const finding = {
      type: 'test-email',
      message: 'Найден тестовый email test@example.com',
      severity: 'high' as const,
      suggestion: 'Это тестовая проверка'
    };
    findings.push(finding);
    logDebug('🧪 Test email detected', finding);
  }
  
  if (text.toLowerCase().includes('макарек')) {
    const finding = {
      type: 'test-word',
      message: 'Найдено тестовое слово "макарек"',
      severity: 'medium' as const,
      suggestion: 'Это тестовая проверка детектора'
    };
    findings.push(finding);
    logDebug('🧪 Test word detected', finding);
  }
  
  logDebug('✅ Analysis completed', { 
    totalFindings: findings.length,
    highRisk: findings.filter(f => f.severity === 'high').length,
    mediumRisk: findings.filter(f => f.severity === 'medium').length,
    findingTypes: findings.map(f => f.type)
  });
  
  return findings;
}

// Create and inject analyze button
function createAnalyzeButton(): HTMLElement {
  const button = document.createElement('button');
  button.innerHTML = '<span>🔍</span><span>Analyze</span>';
  button.title = 'AI Auditor - Анализ безопасности';
  
  button.addEventListener('mouseenter', () => {
    button.style.background = '#4a5568';
    button.style.color = '#ffffff';
  });
  
  button.addEventListener('mouseleave', () => {
    button.style.background = 'transparent';
    button.style.color = '#8e8ea0';
  });
  
  button.addEventListener('click', (e) => {
    // PREVENT DEFAULT to stop form submission
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    
    console.log('AI Auditor: Analyze button clicked');
    
    if (currentAdapter) {
      const text = currentAdapter.getText();
      console.log('AI Auditor: Extracted text:', text ? text.substring(0, 100) + '...' : 'EMPTY');
      
      if (text.trim()) {
        const findings = analyzeText(text);
        showAnalysisResults(findings);
      } else {
        showAnalysisResults([{
          type: 'empty',
          message: 'Текст для анализа не найден. Убедитесь, что вы ввели текст в поле ввода.',
          severity: 'low'
        }]);
      }
    } else {
      console.error('AI Auditor: No adapter found');
    }
    
    return false; // Prevent any form submission
  });
  
  return button;
}

// Show analysis results in overlay
function showAnalysisResults(findings: Finding[]): void {
  logDebug('📊 Showing analysis results', { 
    findingsCount: findings.length,
    severities: findings.map(f => f.severity)
  });
  
  // Send analysis to popup for history
  const messageData = {
    type: 'ANALYSIS_COMPLETED',
    url: window.location.href,
    findings: findings,
    textLength: currentAdapter ? currentAdapter.getText().length : 0
  };
  
  logDebug('📤 Sending analysis to popup', messageData);
  
  chrome.runtime.sendMessage(messageData).catch((error) => {
    logDebug('⚠️ Failed to send message to popup', error);
  });
  // Remove existing overlay
  const existing = document.getElementById('ai-auditor-overlay');
  if (existing) {
    existing.remove();
  }
  
  const overlay = document.createElement('div');
  overlay.id = 'ai-auditor-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    width: 350px;
    max-height: 500px;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    z-index: 10000;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    overflow-y: auto;
  `;
  
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 16px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
  `;
  
  const title = document.createElement('h3');
  title.textContent = `AI Auditor - ${findings.length} findings`;
  title.style.cssText = 'margin: 0; font-size: 16px; color: #111827;';
  
  const closeButton = document.createElement('button');
  closeButton.textContent = '×';
  closeButton.style.cssText = `
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #6b7280;
  `;
  closeButton.addEventListener('click', () => overlay.remove());
  
  header.appendChild(title);
  header.appendChild(closeButton);
  overlay.appendChild(header);
  
  const content = document.createElement('div');
  content.style.padding = '16px';
  
  if (findings.length === 0) {
    const noIssues = document.createElement('p');
    noIssues.textContent = '✅ Проблем не обнаружено';
    noIssues.style.cssText = 'margin: 0; color: #059669; text-align: center;';
    content.appendChild(noIssues);
  } else {
    findings.forEach(finding => {
      const item = document.createElement('div');
      item.style.cssText = `
        margin-bottom: 12px;
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid ${finding.severity === 'high' ? '#ef4444' : finding.severity === 'medium' ? '#f59e0b' : '#10b981'};
        background: ${finding.severity === 'high' ? '#fef2f2' : finding.severity === 'medium' ? '#fffbeb' : '#f0fdf4'};
      `;
      
      const message = document.createElement('div');
      message.textContent = `${finding.severity === 'high' ? '🚨' : finding.severity === 'medium' ? '⚠️' : 'ℹ️'} ${finding.message}`;
      message.style.cssText = 'font-weight: 500; margin-bottom: 4px; color: #111827;';
      
      item.appendChild(message);
      
      if (finding.suggestion) {
        const suggestion = document.createElement('div');
        suggestion.textContent = finding.suggestion;
        suggestion.style.cssText = 'font-size: 14px; color: #6b7280;';
        item.appendChild(suggestion);
      }
      
      content.appendChild(item);
    });
  }
  
  overlay.appendChild(content);
  document.body.appendChild(overlay);
  
  // Auto-hide after 10 seconds
  setTimeout(() => {
    if (document.getElementById('ai-auditor-overlay')) {
      overlay.remove();
    }
  }, 10000);
}

// Settings loaded from storage
let currentSettings = {
  blockOnHighRisk: false,
  offlineMode: true
};

// Load settings from storage
async function loadSettings(): Promise<void> {
  logDebug('⚙️ Loading settings from storage');
  try {
    const result = await chrome.storage.local.get(['settings']);
    if (result.settings) {
      currentSettings = { ...currentSettings, ...result.settings };
      logDebug('✅ Settings loaded successfully', currentSettings);
    } else {
      logDebug('ℹ️ No saved settings found, using defaults', currentSettings);
    }
  } catch (error) {
    logDebug('❌ Failed to load settings', error);
  }
}

// Block modal management
function showBlockModal(findings: Finding[]): Promise<boolean> {
  return new Promise((resolve) => {
    // Remove existing modal
    const existing = document.getElementById('ai-auditor-block-modal');
    if (existing) {
      existing.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = 'ai-auditor-block-modal';
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    `;
    
    const dialog = document.createElement('div');
    dialog.style.cssText = `
      background: white;
      border-radius: 12px;
      max-width: 500px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
      box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    `;
    
    const highRiskFindings = findings.filter(f => f.severity === 'high');
    
    const content = `
      <div style="padding: 24px;">
        <div style="text-align: center; margin-bottom: 20px;">
          <div style="font-size: 48px; margin-bottom: 8px;">🚨</div>
          <h2 style="margin: 0; color: #dc2626; font-size: 20px;">Обнаружены риски безопасности</h2>
        </div>
        
        <div style="margin-bottom: 20px;">
          <p style="color: #374151; margin-bottom: 16px; line-height: 1.5;">
            AI Auditor обнаружил потенциальные проблемы в вашем сообщении:
          </p>
          
          ${highRiskFindings.map(finding => `
            <div style="
              margin-bottom: 12px;
              padding: 12px;
              background: #fef2f2;
              border-left: 4px solid #ef4444;
              border-radius: 6px;
            ">
              <div style="font-weight: 600; color: #dc2626; margin-bottom: 4px;">
                🚨 ${finding.message}
              </div>
              ${finding.suggestion ? `
                <div style="font-size: 14px; color: #6b7280;">
                  ${finding.suggestion}
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
        
        <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
          <p style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.4;">
            💡 <strong>Рекомендация:</strong> Исправьте указанные проблемы перед отправкой. 
            Или отключите строгий режим в настройках расширения.
          </p>
        </div>
        
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
          <button id="block-cancel" style="
            padding: 10px 20px;
            background: #f3f4f6;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            color: #374151;
          ">
            Отменить
          </button>
          <button id="block-override" style="
            padding: 10px 20px;
            background: #dc2626;
            border: 1px solid #dc2626;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            color: white;
          ">
            Отправить всё равно
          </button>
        </div>
      </div>
    `;
    
    dialog.innerHTML = content;
    modal.appendChild(dialog);
    document.body.appendChild(modal);
    
    // Event listeners
    const cancelBtn = document.getElementById('block-cancel');
    const overrideBtn = document.getElementById('block-override');
    
    cancelBtn?.addEventListener('click', () => {
      modal.remove();
      resolve(false); // Don't send
    });
    
    overrideBtn?.addEventListener('click', () => {
      modal.remove();
      resolve(true); // Send anyway
    });
    
    // Close on ESC
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        modal.remove();
        document.removeEventListener('keydown', handleEsc);
        resolve(false);
      }
    };
    document.addEventListener('keydown', handleEsc);
  });
}

// Enhanced analyze function with blocking
async function analyzeAndCheckBlock(text: string): Promise<{ findings: Finding[], shouldBlock: boolean }> {
  const findings = analyzeText(text);
  const hasHighRisk = findings.some(f => f.severity === 'high');
  const shouldBlock = currentSettings.blockOnHighRisk && hasHighRisk;
  
  return { findings, shouldBlock };
}

// Setup blocking logic - more cautious approach
function setupBlockingLogic(): void {
  if (!currentAdapter) return;
  
  console.log('AI Auditor: Setting up blocking logic');
  
  // Monitor for send button clicks for blocking
  const sendButton = currentAdapter.getSendButton();
  if (!sendButton) return;
  
  // Add event listener with high priority (capture phase)
  sendButton.addEventListener('click', async (e) => {
    // Only check if blocking is enabled
    if (!currentSettings.blockOnHighRisk) return;
    
    const text = currentAdapter?.getText() || '';
    if (!text.trim()) return; // Allow empty submissions
    
    console.log('AI Auditor: Checking for blocking, text length:', text.length);
    
    const { findings, shouldBlock } = await analyzeAndCheckBlock(text);
    
    if (shouldBlock) {
      console.log('AI Auditor: BLOCKING submission due to high-risk findings');
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      
      const shouldSend = await showBlockModal(findings);
      if (shouldSend) {
        console.log('AI Auditor: User chose to override block');
        // Create a new click event and dispatch it
        // but first remove our listener to avoid infinite loop
        sendButton.removeEventListener('click', arguments.callee as EventListener);
        sendButton.click();
      }
      return false;
    }
  }, true); // Capture phase for higher priority
}

// Initialize for detected site
function initializeForSite(): void {
  if (!currentAdapter) return;
  
  console.log('AI Auditor: Initializing for', currentAdapter.name);
  
  // Try to inject button
  function tryInject() {
    if (!currentAdapter) return;
    
    const existingButton = document.querySelector('#ai-auditor-analyze-btn');
    if (existingButton) return; // Button already exists
    
    const button = createAnalyzeButton();
    currentAdapter.injectAnalyzeButton(button);
    
    if (document.contains(button)) {
      console.log('AI Auditor: Button injected successfully');
      // Set up blocking logic only AFTER successful injection
      setTimeout(() => setupBlockingLogic(), 500);
    }
  }
  
  // Initial injection attempts with increasing delays
  setTimeout(tryInject, 500);
  setTimeout(tryInject, 1500);
  setTimeout(tryInject, 3000);
  
  // Set up MutationObserver to re-inject on DOM changes
  const observer = new MutationObserver(() => {
    // Check if our button still exists
    const existingButton = document.querySelector('#ai-auditor-analyze-btn');
    if (!existingButton) {
      console.log('AI Auditor: Button disappeared, re-injecting...');
      setTimeout(tryInject, 100);
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// Listen for settings updates from popup
chrome.runtime.onMessage.addListener((message: any, sender: chrome.runtime.MessageSender, sendResponse: (response?: any) => void) => {
  if (message.type === 'SETTINGS_UPDATED') {
    currentSettings = { ...currentSettings, ...message.settings };
  }
});

// Initialize when DOM is ready
logDebug('🚀 Initializing AI Auditor', { 
  readyState: document.readyState,
  url: window.location.href 
});

if (document.readyState === 'loading') {
  logDebug('⏳ Waiting for DOMContentLoaded');
  document.addEventListener('DOMContentLoaded', async () => {
    logDebug('✅ DOM loaded, starting initialization');
    await loadSettings();
    detectSite();
  });
} else {
  logDebug('✅ DOM already loaded, starting immediately');
  loadSettings().then(detectSite);
}

// Also detect on navigation changes (for SPAs)
let lastUrl = location.href;
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl) {
    lastUrl = url;
    setTimeout(detectSite, 1000);
  }
}).observe(document, { subtree: true, childList: true });



