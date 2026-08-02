import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const html = await fs.readFile(new URL('../web/index.html', import.meta.url), 'utf8');
const app = await fs.readFile(new URL('../web/app.js', import.meta.url), 'utf8');
const worker = await fs.readFile(new URL('../web/_worker.js', import.meta.url), 'utf8');

assert.match(html, /data-panel="leaderboard"/);
assert.match(html, /id="leaderboard-worth-chart"/);
assert.match(app, /async function loadLeaderboard/);
assert.match(app, /async function openLeaderboardWallet/);
assert.match(app, /__wallet: true/);
assert.match(app, /#nft-price-chart, #leaderboard-worth-chart/);
assert.match(worker, /leaderboard\\\/\[0-9a-f\]\{40\}\\\/history/);

console.log('Wallet leaderboard and shared NFT chart controls: OK');
