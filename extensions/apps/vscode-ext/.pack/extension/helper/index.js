// AI Auditor Helper Server
const http = require('http');

const port = parseInt(process.argv[2] || '43111', 10);

const server = http.createServer(async (req, res) => {
  // Health check endpoint
  if (req.url === '/health') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ ok: true, port, timestamp: new Date().toISOString() }));
    return;
  }
  
  // Analyze endpoint
  if (req.method === 'POST' && req.url === '/analyze') {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
      if (body.length > 5e6) req.destroy(); // Limit to 5MB
    });
    req.on('end', () => {
      try {
        const { text } = JSON.parse(body || '{}');
        const input = String(text || '');
        
        // Mock analysis with simple heuristics
        const findings = [];
        if (input.length > 4000) {
          findings.push({ kind: 'length', message: 'Text is quite long; consider shortening.' });
        }
        if (/password|api[_\- ]?key/i.test(input)) {
          findings.push({ kind: 'pii', message: 'Potential secret-like token detected.' });
        }
        
        const revised = input.replace(/\s+$/gm, '').trim();
        
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ 
          revised, 
          findings,
          suggestions: findings.map(f => `Fix: ${f.message}`)
        }));
      } catch (e) {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON in request body' }));
      }
    });
    return;
  }
  
  // 404 for unknown routes
  res.writeHead(404, { 'content-type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(port, '127.0.0.1', () => {
  console.log(`AI Auditor Helper Server running on http://127.0.0.1:${port}`);
  console.log(`Endpoints: /health, /analyze`);
});


