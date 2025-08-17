import type { AnalysisRequest, AnalysisResult } from './types';
import { MSG } from '@extensions/messaging';
import { runLengthDetector, runPiiDetector } from '@extensions/core';
import { ApiClient } from './apiClient';
const client = new ApiClient();
client.loadConfig();

chrome.runtime.onInstalled.addListener(async () => {
  try { await chrome.storage.local.set({ lastReadyAt: Date.now() }); } catch {}
});

chrome.runtime.onMessage.addListener((msg: any, _sender: chrome.runtime.MessageSender, sendResponse: (resp: any) => void) => {
  (async () => {
    if (msg?.type === MSG.ANALYZE_PROMPT) {
      const lastReadyAt = Date.now();
      await chrome.storage.local.set({ lastReadyAt });
      const req = msg.payload as AnalysisRequest;
      // quick local heuristics first
      const localFindings = [...runLengthDetector(req.text), ...runPiiDetector(req.text)]
        .map(f => ({
          severity: f.severity === 'high' ? 'error' : f.severity === 'medium' ? 'warn' : 'info',
          message: f.message,
        }));
      const remote = await client.analyze(req);
      const merged: AnalysisResult = remote.ok
        ? { ok: true, findings: [...localFindings, ...remote.findings] as { message: string; severity: 'info' | 'warn' | 'error'; hint?: string; start?: number; end?: number }[] }
        : remote;
      const result: AnalysisResult = merged;
      await chrome.storage.local.set({ lastResult: result, lastRequest: req });
      sendResponse({ ok: true, result });
      return;
    }
    sendResponse({ ok: false, error: 'Unknown message' });
  })().catch(err => sendResponse({ ok: false, error: String(err?.message || err) }));
  return true;
});


