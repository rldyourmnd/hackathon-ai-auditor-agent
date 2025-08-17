import { describe, it, expect, vi } from 'vitest';
import { createClient, TimeoutError, RateLimitError, ServerError } from '../src/index.js';

function makeFetch(sequence: Array<{ status: number; body?: any; headers?: Record<string, string> }>) {
  let i = 0;
  return async (_url: any, _init: any) => {
    const item = sequence[i++] ?? sequence[sequence.length - 1];
    const headers = new Headers({ 'content-type': 'application/json', ...(item.headers || {}) });
    return new Response(JSON.stringify(item.body ?? {}), { status: item.status, headers });
  };
}

describe('client-sdk retry/timeout', () => {
  it('retries on 500 then succeeds', async () => {
    const client = createClient({
      baseUrl: 'http://localhost',
      getApiKey: async () => 'k',
      fetchLike: makeFetch([
        { status: 500 },
        { status: 200, body: { findings: [] } },
      ]) as any,
      envMetaProvider: () => ({ env: 'vscode', extensionVersion: '0.0.1' }),
      retry: { baseDelayMs: 1, maxDelayMs: 2 },
    });
    const res = await client.analyze({ text: 'x' });
    expect(res.findings).toBeDefined();
  });

  it('maps 429 with retry-after', async () => {
    const client = createClient({
      baseUrl: 'http://localhost',
      getApiKey: async () => 'k',
      fetchLike: makeFetch([
        { status: 429, headers: { 'retry-after': '2' } },
      ]) as any,
      envMetaProvider: () => ({ env: 'vscode', extensionVersion: '0.0.1' }),
      retry: { maxAttempts: 1 },
    });
    await expect(client.analyze({ text: 'x' })).rejects.toBeInstanceOf(RateLimitError);
  });
});


