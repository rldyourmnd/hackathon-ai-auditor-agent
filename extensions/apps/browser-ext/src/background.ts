// Minimal background service worker for MV3
console.log('AI Auditor background service worker loaded');

// Lazy import to avoid MV3 eval/import issues
async function getClient() {
  const { createClient } = await import('@extensions/client-sdk');
  return createClient({
    baseUrl: 'http://localhost:8000/api',
    getApiKey: async () => {
      // Example: read from chrome.storage.local
      try {
        const data = await chrome.storage.local.get('AI_AUDITOR_API_KEY');
        return (data?.AI_AUDITOR_API_KEY as string | undefined) ?? null;
      } catch {
        return null;
      }
    },
    envMetaProvider: () => ({ env: 'mv3', extensionVersion: '0.0.1' }),
    fetchLike: fetch,
    idempotency: { enabled: true },
    timeoutMs: 20000,
  });
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    if (msg?.type === 'ai-auditor/analyze') {
      const client = await getClient();
      const res = await client.analyze({ text: String(msg.text || '') });
      sendResponse({ ok: true, res });
    }
  })().catch(err => sendResponse({ ok: false, error: String(err?.message || err) }));
  return true; // async response
});


