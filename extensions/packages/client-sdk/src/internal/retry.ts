export function backoffDelayMs(base: number, attempt: number, jitter: number): number {
  const exp = base * Math.pow(2, Math.max(0, attempt - 1));
  const rand = Math.random() * (exp * jitter);
  return exp + rand;
}

export function shouldRetry(err: unknown): boolean {
  // Network-like
  const msg = String((err as any)?.message || '');
  if (msg.includes('Network') || msg.includes('fetch') || msg.includes('Failed to fetch')) return true;
  // Typed errors by name
  const name = (err as any)?.name as string | undefined;
  if (name === 'TimeoutError' || name === 'RateLimitError' || name === 'ServerError') return true;
  // HTTP-like retryable
  if ((err as any)?.status && typeof (err as any).status === 'number') {
    const s = (err as any).status as number;
    if (s >= 500 || s === 429) return true;
  }
  return false;
}


