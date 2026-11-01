// One Chromium process shared by Playwright MCP and Chrome DevTools MCP.
const {chromium} = require('/app/node_modules/playwright-core');
const {spawn} = require('node:child_process');
const net = require('node:net');

(async () => {
  const browser = await chromium.launch({
    channel: 'chromium', headless: true,
    args: ['--remote-debugging-port=9222', '--no-sandbox'],
  });
  // Internal Docker-only access for Hermes; no CDP port is published on the host.
  net.createServer(client => {
    const upstream = net.connect(9222, '127.0.0.1');
    client.on('error', () => upstream.destroy());
    upstream.on('error', () => client.destroy());
    client.on('close', () => upstream.destroy());
    upstream.on('close', () => client.destroy());
    client.pipe(upstream).pipe(client);
  }).listen(9223, '0.0.0.0');
  const server = spawn(process.execPath, [
    '/app/cli.js', '--cdp-endpoint', 'http://127.0.0.1:9222',
    '--shared-browser-context', '--caps', 'devtools,pdf,vision',
    '--port', '8931', '--host', '0.0.0.0',
    '--allowed-hosts', 'localhost:8931,127.0.0.1:8931,playwright:8931',
  ], {stdio: 'inherit'});
  let closing = false;
  const close = async (code = 0) => {
    if (closing) return;
    closing = true;
    server.kill('SIGTERM');
    await browser.close();
    process.exit(code);
  };
  process.on('SIGTERM', () => close());
  process.on('SIGINT', () => close());
  server.on('exit', code => close(code || 0));
})().catch(error => {
  console.error('Browser tool startup failed:', error.message);
  process.exit(1);
});
