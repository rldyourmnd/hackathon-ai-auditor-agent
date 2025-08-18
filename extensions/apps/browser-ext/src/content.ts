import type { AnalysisRequest, AnalysisResult } from './types';
import { MSG, type AnalyzePromptMessage } from '@extensions/messaging';
import { ChatGPTAdapter } from '@extensions/adapters';

const A = ChatGPTAdapter;
const IDS = { btn: '__ai_auditor_btn__', toast: '__ai_auditor_toast__', style: '__ai_auditor_style__' } as const;

function ensureStyles() {
  if (document.getElementById(IDS.style)) return;
  const style = document.createElement('style');
  style.id = IDS.style;
  style.textContent = `
    #${IDS.btn}{display:inline-flex;align-items:center;gap:.4rem;padding:.35rem .6rem;border-radius:10px;border:1px solid rgba(0,0,0,.15);background:rgba(255,255,255,.85);backdrop-filter:blur(6px);font:500 12px/1.2 system-ui,sans-serif;cursor:pointer}
    #${IDS.btn}:hover{background:#fff}
    #${IDS.toast}{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);padding:.5rem .75rem;border-radius:10px;background:rgba(0,0,0,.85);color:#fff;font:500 12px/1 system-ui,sans-serif;opacity:0;transition:.18s;z-index:2147483647}
    #${IDS.toast}.show{opacity:1}
    #${IDS.toast}[data-kind="err"]{background:rgba(200,0,0,.85)}
  `;
  document.head.appendChild(style);
}

function ensureButton() {
  if (document.getElementById(IDS.btn)) return;
  const send = A.findSendButton();
  if (!send) return;
  const btn = document.createElement('button');
  btn.id = IDS.btn;
  btn.type = 'button';
  btn.textContent = 'Audit';
  btn.setAttribute('aria-label', 'Audit prompt');
  A.anchorForButton(send).insertBefore(btn, send);
  btn.addEventListener('click', analyzeAndMaybeSend);
  document.addEventListener('keydown', (e) => {
    if (e.altKey && (e.key.toLowerCase() === 'a')) {
      const input = A.findInput();
      const focused = document.activeElement;
      if (input && (focused === input || input.contains(focused))) {
        e.preventDefault();
        analyzeAndMaybeSend();
      }
    }
  }, { capture: true });
}

function toast(message: string, kind: 'ok' | 'err' = 'ok') {
  let t = document.getElementById(IDS.toast);
  if (!t) { t = document.createElement('div'); t.id = IDS.toast; document.body.appendChild(t); }
  t.textContent = message; t.setAttribute('data-kind', kind); t.classList.add('show');
  setTimeout(() => t && t.classList.remove('show'), 2000);
}

async function analyzeAndMaybeSend() {
  const input = A.findInput();
  if (!input) return toast('Input not found', 'err');
  const text = A.getDraft(input).trim();
  if (!text) return toast('Nothing to analyze', 'err');
  const req: AnalysisRequest = { text, source: 'chatgpt', url: location.href, ts: Date.now() };
  toast('Analyzing…');
  const res = await chrome.runtime.sendMessage({ type: MSG.ANALYZE_PROMPT, payload: req } satisfies AnalyzePromptMessage)
    .catch(() => null) as { ok: boolean; result?: AnalysisResult } | null;
  if (!res?.ok || !res.result) return toast('Analyzer error', 'err');
  if (res.result.ok) {
    const issues = res.result.findings.length;
    toast(`Findings: ${issues}`);
  } else {
    toast(`Error: ${res.result.error}`, 'err');
  }
}

function mount() {
  if (!A.matches(location)) return;
  ensureStyles();
  ensureButton();
}

mount();
const mo = new MutationObserver(() => mount());
mo.observe(document.documentElement, { childList: true, subtree: true });



