import assert from 'node:assert/strict';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const pwa = fs.readFileSync(new URL('../web/pwa.js', import.meta.url), 'utf8');
const html = fs.readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');

assert.match(pwa, /Download Helix Wallet for Windows/);
assert.match(pwa, /\/downloads\/helix-wallet-windows\.zip/);
assert.match(pwa, /\/downloads\/helix-wallet-linux\.zip/);
assert.match(pwa, /if \(!standalone && !isMobile && \(isWindows \|\| isLinux\)\) showDesktopDownload\(\)/);
assert.match(html, /pwa\.js\?v=4/);
assert.match(html, /Windows Wallet App/);
assert.ok(fs.statSync(new URL('../web/downloads/HelixWallet.exe', import.meta.url)).size > 1_000_000);
assert.ok(fs.statSync(new URL('../web/downloads/HelixMiner.exe', import.meta.url)).size > 1_000_000);
assert.ok(fs.statSync(new URL('../web/downloads/HelixNodeSetup.exe', import.meta.url)).size > 1_000_000);

const linuxArchive = new URL('../web/downloads/helix-wallet-linux.zip', import.meta.url);
const listing = execFileSync('tar', ['-tvf', linuxArchive.pathname.replace(/^\/(?:[A-Za-z]:)/, value => value.slice(1))], { encoding: 'utf8' });
assert.match(listing, /-rwxr-xr-x.*linux-wallet\/helix-wallet\s*$/m);
assert.match(listing, /-rwxr-xr-x.*linux-wallet\/install-helix-wallet\.sh\s*$/m);

console.log('Desktop application downloads: OK');
