import type { SiteAdapter } from './siteAdapter';

export const ChatGPTAdapter: SiteAdapter = {
  id: 'chatgpt',
  matches: (loc) => /chat\.openai\.com|chatgpt\.com/.test(loc.host),
  findInput(doc = document) {
    const ta = doc.querySelector('form textarea');
    if (ta instanceof HTMLTextAreaElement && ta.offsetParent) return ta;
    const ed = doc.querySelector('form [contenteditable="true"]') as HTMLElement | null;
    return ed && ed.offsetParent ? ed : null;
  },
  findSendButton(doc = document) {
    const sel = [
      'form button[type="submit"]',
      'form button[data-testid="send-button"]',
      'form button[aria-label*="Send"]',
      'form button[aria-label*="Отправ"]',
    ].join(',');
    const btns = Array.from(doc.querySelectorAll<HTMLButtonElement>(sel));
    return btns.find(b => b.offsetParent && !b.disabled) || null;
  },
  getDraft(el) {
    return el instanceof HTMLTextAreaElement ? el.value : (el.textContent ?? '').replace(/\u00A0/g, ' ');
  },
  setDraft(el, text) {
    if (el instanceof HTMLTextAreaElement) el.value = text; else el.textContent = text;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  },
  anchorForButton(sendBtn) {
    return sendBtn.parentElement ?? sendBtn;
  },
};


