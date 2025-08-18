export * from './siteAdapter';
export { ChatGPTAdapter } from './chatgpt';
import type { SiteAdapter } from './siteAdapter';
import { ChatGPTAdapter as ChatGPT } from './chatgpt';

export const adapters: SiteAdapter[] = [ ChatGPT ];
export function getActiveAdapter(): SiteAdapter | null {
  for (const a of adapters) if (a.matches(location)) return a;
  return null;
}


