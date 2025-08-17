import type { BrowserAnalysisRequest as AnalysisRequest, BrowserAnalysisResult as AnalysisResult, BrowserAnalysisResponseOk as AnalysisResponse } from '@extensions/shared';
import { SettingsSchema, loadSettings } from '@extensions/shared';
import { createBrowserApiClient } from '@extensions/client-sdk';

type Mode = 'mock' | 'remote';

async function mockAnalyze(req: AnalysisRequest): Promise<AnalysisResponse> {
  const findings: AnalysisResponse['findings'] = [];
  if (req.text.length > 1200) {
    findings.push({ severity: 'warn', message: 'Prompt is long; consider trimming.' });
  }
  if (/\bTODO\b/i.test(req.text)) {
    findings.push({ severity: 'info', message: 'Found "TODO" — clarify requirements.', hint: 'Replace TODOs with concrete constraints.' });
  }
  if (findings.length === 0) {
    findings.push({ severity: 'info', message: 'No obvious issues detected.' });
  }
  return new Promise(resolve => setTimeout(() => resolve({ ok: true, findings }), 400));
}

export class ApiClient {
  private mode: Mode = 'mock';
  private baseUrl = '';
  private apiKey = '';

  async loadConfig() {
    const cfg = await loadSettings().catch(async () => {
      const legacy = await chrome.storage.local.get(['mode', 'baseUrl', 'apiKey']);
      return SettingsSchema.parse({
        version: 1,
        mode: (legacy.mode as Mode) || 'mock',
        baseUrl: (legacy.baseUrl as string) || '',
        apiKey: (legacy.apiKey as string) || '',
        autoAnalyzeOnPaste: false,
        maxLength: 2000,
        flags: { enableMock: true, enableInlineHints: false },
      });
    });
    this.mode = cfg.mode as Mode;
    this.baseUrl = cfg.baseUrl;
    this.apiKey = cfg.apiKey;
  }

  async analyze(req: AnalysisRequest): Promise<AnalysisResult> {
    if (this.mode === 'mock' || !this.baseUrl) return mockAnalyze(req);
    const client = createBrowserApiClient({
      baseUrl: this.baseUrl,
      getApiKey: async () => this.apiKey || null,
      timeoutMs: 20000,
      idempotency: { enabled: true },
      fetchLike: fetch,
    });
    return client.analyzeBrowser(req);
  }
}


