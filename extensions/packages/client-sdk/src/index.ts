import { uuidv4 } from './internal/uuidv4.js';
import { buildHeaders, mergeHeaders } from './internal/headers.js';
import { backoffDelayMs, shouldRetry } from './internal/retry.js';
import type { BrowserAnalysisRequest, BrowserAnalysisResult } from '@extensions/shared';

export type Severity = 'low' | 'medium' | 'high';

export interface Finding { id: string; rule: string; severity: Severity; range?: [number, number]; message: string; }
export interface Suggestion { id: string; title: string; patch?: string; rationale?: string; }

export interface AnalyzeRequest {
  text: string;
  lang?: 'ru' | 'en';
  detectors?: string[];
  flags?: Partial<Record<string, unknown>>;
  model?: string;
  context?: Record<string, unknown>;
  correlationId?: string;
}

export interface AnalyzeResponse {
  findings: Finding[];
  suggestions?: Suggestion[];
  latencyMs?: number;
  limits?: { inputChars?: number };
  traceId?: string;
  cost?: { inputTokens?: number; outputTokens?: number; currency?: 'USD' };
}

export interface ReviseRequest extends AnalyzeRequest {}
export interface ReviseResponse extends AnalyzeResponse { revisedText?: string }

export interface EnvMeta {
  env: 'mv3' | 'vscode';
  extensionVersion: string;
  coreVersion?: string;
  os?: string;
  userAgentSanitized?: string;
}

export interface RetryPolicy {
  maxAttempts?: number; // total attempts including first
  baseDelayMs?: number;
  maxDelayMs?: number;
  maxElapsedMs?: number;
  jitter?: number; // 0..1
}

export interface ClientConfig {
  baseUrl: string;
  getApiKey: () => Promise<string | null>;
  transport?: 'rest' | 'grpc-web' | 'ws';
  timeoutMs?: number;
  retry?: RetryPolicy;
  headers?: Record<string, string>;
  envMetaProvider?: () => EnvMeta;
  idempotency?: { enabled: boolean; headerName?: string };
  fetchLike?: (input: RequestInfo, init?: RequestInit) => Promise<Response>;
}

export interface CallOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
  headers?: Record<string, string>;
  idempotencyKey?: string;
  priority?: 'low' | 'normal' | 'high';
}

export type Transport = (
  route: 'analyze' | 'revise',
  body: unknown,
  opts: Required<Pick<ClientConfig, 'baseUrl' | 'fetchLike'>> & {
    apiKey: string | null;
    headers: Record<string, string>;
    timeoutMs: number;
    retry: Required<RetryPolicy>;
    idempotencyHeader?: { name: string; value: string };
    signal?: AbortSignal;
  }
) => Promise<unknown>;

export class TimeoutError extends Error { cause?: unknown }
export class NetworkError extends Error { cause?: unknown }
export class UnauthorizedError extends Error {}
export class RateLimitError extends Error { retryAfterSec?: number }
export class ServerError extends Error { status!: number; body?: unknown }
export class ValidationError extends Error { details?: unknown }

function normalizeRetryPolicy(retry?: RetryPolicy): Required<RetryPolicy> {
  return {
    maxAttempts: Math.max(1, retry?.maxAttempts ?? 3),
    baseDelayMs: retry?.baseDelayMs ?? 250,
    maxDelayMs: retry?.maxDelayMs ?? 5_000,
    maxElapsedMs: retry?.maxElapsedMs ?? 20_000,
    jitter: retry?.jitter ?? 0.2,
  };
}

export function restTransport(fetchLike: NonNullable<ClientConfig['fetchLike']>): Transport {
  return async (route, body, opts) => {
    const url = opts.baseUrl.replace(/\/$/, '') + '/' + route;
    const controller = new AbortController();
    const external = opts.signal;
    const timeout = setTimeout(() => controller.abort(), opts.timeoutMs);
    const onAbort = () => controller.abort();
    external?.addEventListener('abort', onAbort, { once: true });

    const start = Date.now();
    let attempt = 0;
    let lastErr: unknown;
    try {
      while (true) {
        attempt++;
        try {
          const headers = new Headers(opts.headers);
          if (opts.apiKey) headers.set('Authorization', `Bearer ${opts.apiKey.replace(/\s+/g, '')}`);
          headers.set('Content-Type', 'application/json');
          headers.set('Accept', 'application/json');

          const res = await fetchLike(url, {
            method: 'POST',
            headers,
            body: JSON.stringify(body),
            signal: controller.signal,
          });

          if (res.status === 401) throw new UnauthorizedError('Unauthorized');
          if (res.status === 429) {
            const e = new RateLimitError('Rate limited');
            const ra = res.headers.get('retry-after');
            if (ra) {
              const sec = /\d+/.test(ra) ? parseInt(ra, 10) : Math.ceil((Date.parse(ra) - Date.now()) / 1000);
              if (!Number.isNaN(sec)) e.retryAfterSec = sec;
            }
            throw e;
          }
          if (res.status >= 500) {
            const se = new ServerError('Server error');
            se.status = res.status;
            try { se.body = await res.json(); } catch {}
            throw se;
          }
          if (!res.ok) {
            const se = new ServerError(`HTTP ${res.status}`);
            se.status = res.status;
            try { se.body = await res.json(); } catch {}
            throw se;
          }
          const contentType = res.headers.get('content-type') || '';
          if (!contentType.includes('application/json')) {
            throw new ValidationError('Unexpected content-type');
          }
          return await res.json();
        } catch (err) {
          lastErr = err;
          if (controller.signal.aborted) throw new TimeoutError('Request timeout');
          const elapsed = Date.now() - start;
          if (!shouldRetry(err) || attempt >= opts.retry.maxAttempts || elapsed >= opts.retry.maxElapsedMs) {
            throw err;
          }
          const delay = Math.min(backoffDelayMs(opts.retry.baseDelayMs, attempt, opts.retry.jitter), opts.retry.maxDelayMs);
          await new Promise(r => setTimeout(r, delay));
          continue;
        }
      }
    } finally {
      clearTimeout(timeout);
      external?.removeEventListener('abort', onAbort as any);
    }
  };
}

export interface LocalAnalyzer {
  analyze(req: AnalyzeRequest): Promise<AnalyzeResponse>;
  revise?(req: ReviseRequest): Promise<ReviseResponse>;
}

export function offlineTransport(analyzer: LocalAnalyzer): Transport {
  return async (route, body) => {
    const req = body as any;
    if (route === 'analyze') return analyzer.analyze(req);
    if (route === 'revise') {
      if (typeof analyzer.revise === 'function') return analyzer.revise(req);
      const r: ReviseResponse = { findings: [], suggestions: [] };
      return r;
    }
    throw new ValidationError('Unknown route');
  };
}

export function createClient(config: ClientConfig) {
  const fetchLike = config.fetchLike ?? (globalThis as any).fetch?.bind(globalThis);
  if (!fetchLike && (config.transport ?? 'rest') === 'rest') {
    throw new ValidationError('fetchLike is required for REST transport');
  }
  const retry = normalizeRetryPolicy(config.retry);

  const baseHeaders = buildHeaders({
    staticHeaders: config.headers,
    envMeta: config.envMetaProvider?.(),
  });

  const transportImpl: Transport = (config.transport ?? 'rest') === 'rest'
    ? restTransport(fetchLike!)
    : (() => { throw new ValidationError('Only rest transport is implemented'); }) as any;

  async function call(route: 'analyze' | 'revise', body: any, opts?: CallOptions): Promise<any> {
    const apiKey = await config.getApiKey();
    if (!apiKey) throw new UnauthorizedError('API key not configured');

    const headers = mergeHeaders(baseHeaders, opts?.headers);
    const timeoutMs = opts?.timeoutMs ?? config.timeoutMs ?? 20_000;
    const idemp = config.idempotency?.enabled
      ? { name: config.idempotency.headerName ?? 'Idempotency-Key', value: opts?.idempotencyKey ?? uuidv4() }
      : undefined;

    return transportImpl(route, body, {
      baseUrl: config.baseUrl,
      fetchLike: fetchLike!,
      apiKey,
      headers,
      timeoutMs,
      retry,
      idempotencyHeader: idemp,
      signal: opts?.signal,
    });
  }

  return {
    analyze: (req: AnalyzeRequest, opts?: CallOptions) => call('analyze', {
      ...req,
      correlationId: req.correlationId ?? uuidv4(),
      schemaVersion: 1,
    }, opts) as Promise<AnalyzeResponse>,
    revise: (req: ReviseRequest, opts?: CallOptions) => call('revise', {
      ...req,
      correlationId: req.correlationId ?? uuidv4(),
      schemaVersion: 1,
    }, opts) as Promise<ReviseResponse>,
    cancel: (_token: unknown) => { /* token-based cancel could be wired later */ },
  };
}

// Convenience wrapper that conforms to browser extension UI contracts
export function createBrowserApiClient(config: Omit<ClientConfig, 'transport'> & { localAnalyzer?: LocalAnalyzer }) {
  const transport = config.localAnalyzer ? offlineTransport(config.localAnalyzer) : restTransport(config.fetchLike ?? fetch.bind(globalThis));
  const internal = createClient({ ...config, transport: 'rest' });
  return {
    async analyzeBrowser(req: BrowserAnalysisRequest, opts?: CallOptions): Promise<BrowserAnalysisResult> {
      try {
        const coreReq: AnalyzeRequest = { text: req.text };
        const coreRes = await internal.analyze(coreReq, opts);
        const findings = (coreRes.findings ?? []).map(f => ({
          severity: (f.severity === 'high' ? 'error' : f.severity === 'medium' ? 'warn' : 'info') as any,
          message: f.message,
        }));
        return { ok: true, findings };
      } catch (e: any) {
        return { ok: false, error: String(e?.message || e) } as const;
      }
    }
  };
}

// internal helpers re-export (optional minimal)
export { buildHeaders } from './internal/headers';


