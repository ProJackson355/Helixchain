import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const readme = fs.readFileSync(new URL('../README.md', import.meta.url), 'utf8');

assert.match(html, /data-panel="docs"/);
assert.match(html, /id="panel-docs"/);
assert.match(html, /href="\/downloads\/helix-miner\.zip"/);
assert.match(html, /href="\/downloads\/helix-node\.zip"/);
assert.match(html, /href="\/downloads\/helix-pool\.zip"/);
assert.match(html, /href="\/downloads\/helix-wallet-windows\.zip"/);
assert.match(html, /href="\/downloads\/helix-wallet-linux\.zip"/);
assert.match(html, /Run a full node/);
assert.match(html, /Mine with Helix Miner/);
assert.match(html, /helix_miner_cli\.py --address/);
assert.match(html, /Supported GPUs/);
assert.match(html, /compute capability 3\.0 or newer/);
assert.match(html, /AMD, Intel, Apple Silicon/);
assert.match(html, /Expose and connect a node/);
assert.match(html, /id="btn-submit-node"/);
assert.match(html, /Submit your node for the shared list/);
assert.match(readme, /## Updates/);
assert.ok(fs.statSync(new URL('../web/downloads/helix-miner.zip', import.meta.url)).size > 0);
assert.ok(fs.statSync(new URL('../web/downloads/helix-node.zip', import.meta.url)).size > 0);
assert.ok(fs.statSync(new URL('../web/downloads/helix-pool.zip', import.meta.url)).size > 0);
assert.ok(fs.statSync(new URL('../web/downloads/helix-wallet-windows.zip', import.meta.url)).size > 0);
assert.ok(fs.statSync(new URL('../web/downloads/helix-wallet-linux.zip', import.meta.url)).size > 0);

console.log('Public documentation and downloads: OK');
