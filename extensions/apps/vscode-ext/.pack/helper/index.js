// Minimal local helper server with /health and /analyze mock
const http = require('http');

const port = parseInt(process.argv[2] || '43111', 10);

const server = http.createServer(async (req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ ok: true }));
    return;
  }
  if (req.url === '/analyze' && req.method === 'POST') {
    let body = '';
    req.on('data', (c) => { body += c; if (body.length > 5e6) req.destroy(); });
    req.on('end', () => {
      try {
        const { text } = JSON.parse(body || '{}');
        const revised = String(text || '').replace(/\s+$/gm, '').trim();
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ revised }));
      } catch (e) {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ error: 'bad request' }));
      }
    });
    return;
  }
  res.writeHead(404); res.end();
});

server.listen(port, '127.0.0.1');

// Tiny helper HTTP server (placeholder). Real build would bundle per-OS binaries.
const http = require('http');

const port = parseInt(process.argv[2] || '43111', 10);

const server = http.createServer(async (req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ ok: true }));
    return;
  }
  if (req.method === 'POST' && req.url === '/analyze') {
    let body = '';
    req.on('data', (c) => (body += c));
    req.on('end', () => {
      // Mock analysis result
      const input = JSON.parse(body || '{}').text || '';
      const revised = input.trim() ? input.trim() + ' [revised]' : input;
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ findings: [], suggestions: [], revised }));
    });
    return;
  }
  res.writeHead(404); res.end();
});

server.listen(port, '127.0.0.1');


