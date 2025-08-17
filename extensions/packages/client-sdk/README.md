# @extensions/client-sdk

Unified SDK for MV3 + VS Code.

Usage:

```ts
import { createClient } from '@extensions/client-sdk';

const client = createClient({
  baseUrl: 'http://localhost:8000/api',
  getApiKey: async () => localStorage.getItem('API_KEY'),
  envMetaProvider: () => ({ env: 'mv3', extensionVersion: '0.0.1' }),
  fetchLike: fetch,
});

const res = await client.analyze({ text: 'hello' });
console.log(res.findings);
```


