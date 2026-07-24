import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync(new URL('../web_old/index.html', import.meta.url), 'utf8');
const script = fs.readFileSync(new URL('../web_old/app.js', import.meta.url), 'utf8');

assert.match(html, /id="tx-modal"/);
assert.match(script, /async function openTransactionDetails\(txId\)/);
assert.match(script, /api\('GET', `\/transaction\/\$\{encodeURIComponent\(txId\)\}`\)/);
assert.match(script, /data-tx-id="\$\{escapeHtml\(tx\.tx_id \|\| ''\)\}"/);
assert.match(script, /Confirmations/);
assert.match(script, /Block hash/);
assert.match(script, /Signature/);
assert.match(script, /Public key/);
assert.match(html, /data-panel="activity"/);
assert.match(html, /id="panel-activity"/);
assert.match(html, /id="activity-list"/);
assert.match(html, /id="activity-pagination"/);
assert.match(script, /function renderActivityTransactions\(result\)/);
assert.match(script, /transactions\/recent\?limit=\$\{ACTIVITY_PAGE_SIZE\}&offset=\$\{offset\}/);
assert.match(script, /data-activity-page/);
assert.match(html, /All confirmed transactions from every wallet, newest first/);

console.log('Transaction details UI contract: OK');
