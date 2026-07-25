import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const app = fs.readFileSync(new URL('../web/app.js', import.meta.url), 'utf8');

assert.match(html, /id="btn-mobile-nav"[^>]+aria-controls="main-nav"/);
assert.match(html, /id="mobile-nav-backdrop"/);
assert.match(html, /id="btn-close-mobile-nav"/);
assert.match(html, /id="btn-mobile-logout"/);
assert.match(html, /\.mobile-nav-open #main-nav \{ transform:translateX\(0\)/);
assert.match(html, /header \{[^}]*z-index:40;/);
assert.match(html, /\.mobile-nav-backdrop \{[^}]*z-index:35;/);
assert.match(html, /#panel-nodes > \.nodes-grid \{ grid-template-columns:minmax\(0,1fr\)/);
assert.equal((html.match(/class="nodes-grid"/g) || []).length, 2);
assert.match(app, /function setMobileNav\(open\)/);
assert.match(app, /showPanel\('dashboard'\)/);
assert.match(app, /document\.body\.classList\.add\('wallet-unlocked'\)/);
assert.match(app, /if \(event\.key === 'Escape'/);

console.log('Mobile navigation and Nodes layout: OK');
