import type { EnvMeta } from '../index.js';

export function buildHeaders(params: { staticHeaders?: Record<string, string>; envMeta?: EnvMeta }): Record<string, string> {
  const out: Record<string, string> = {};
  if (params.staticHeaders) {
    for (const [k, v] of Object.entries(params.staticHeaders)) {
      if (v != null) out[k] = String(v);
    }
  }
  const m = params.envMeta;
  if (m) {
    out['X-Client-Env'] = m.env;
    if (m.extensionVersion) out['X-Client-Version'] = m.extensionVersion;
    if (m.coreVersion) out['X-Core-Version'] = m.coreVersion;
    if (m.os) out['X-Platform'] = m.os;
    if (m.userAgentSanitized) out['X-User-Agent'] = m.userAgentSanitized;
  }
  return out;
}

export function mergeHeaders(base?: Record<string, string>, extra?: Record<string, string>): Record<string, string> {
  return { ...(base || {}), ...(extra || {}) };
}


