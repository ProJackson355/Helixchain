import assert from "node:assert/strict";
import fs from "node:fs/promises";

const html = await fs.readFile(new URL("../web/index.html", import.meta.url), "utf8");
const script = await fs.readFile(new URL("../web/app.js", import.meta.url), "utf8");

assert.match(html, /<script src="\/app\.js(?:\?v=[^"]+)?" defer><\/script>/);
assert.doesNotMatch(html, /data-panel="mine"|id="panel-mine"|id="btn-mine"/);
assert.doesNotMatch(script, /\/mine\/start\?address=|\/mine\/status\//);
assert.match(html, /id="panel-send"[\s\S]*?id="pending-list"/);
assert.match(html, /id="pending-alert"/);
assert.match(script, /data-cancel-tx-id/);
assert.match(script, /action: 'cancel_pending'/);
assert.match(script, /\/transaction\/\$\{txId\}\/cancel/);

console.log("Website mining removal and pending cancellation tests: OK");
