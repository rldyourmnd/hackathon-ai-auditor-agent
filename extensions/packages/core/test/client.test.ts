import { createOfflineClient } from '../src/client/client';

test('offline client analyze returns sample findings', async () => {
  const client = createOfflineClient();
  const res = await client.analyze({ text: 'hello world' });
  expect(res.findings.length).toBeGreaterThan(0);
  expect(res.provider).toBe('offline');
});


