import assert from "node:assert/strict";
import fs from "node:fs/promises";

const html = await fs.readFile(new URL("../web/index.html", import.meta.url), "utf8");
const script = await fs.readFile(new URL("../web/app.js", import.meta.url), "utf8");
const headers = await fs.readFile(new URL("../web/_headers", import.meta.url), "utf8");

assert.doesNotMatch(html, /\son(?:click|error|load)\s*=/i);
assert.match(html, /<script src="\/app\.js(?:\?v=[^"]*)?" defer><\/script>/);
assert.doesNotMatch(html, /<script>([\s\S]*?)<\/script>/);
const alertFunction = script.match(/function setAlert\([\s\S]*?\n}/)?.[0];
assert.ok(alertFunction, "setAlert helper should exist");
assert.match(alertFunction, /alert\.textContent = String\(message\);/);
assert.doesNotMatch(alertFunction, /innerHTML/);
assert.match(script, /escapeHtml\(u\.error \|\| 'unreachable'\)/);
assert.match(script, /escapeHtml\(c\.reason \|\| 'Conflict'\)/);
assert.match(script, /escapeHtml\(short\(tx\.sender\)\)/);
assert.match(script, /const WALLET_KDF_ITERATIONS = 600000;/);
assert.match(script, /seedIvHex = _hexRandom\(12\)/);
assert.match(script, /seedCipherHex: await _encryptString\(seedPhrase, aesKey, seedIv\)/);
assert.match(script, /iterations < WALLET_KDF_ITERATIONS \|\| !entry\.seedIvHex/);
assert.match(headers, /script-src-attr 'none'/);
const csp = headers.match(/Content-Security-Policy:\s*([^\n]+)/)?.[1] || "";
const scriptDirective = csp.split(";").find(value => value.trim().startsWith("script-src ")) || "";
assert.doesNotMatch(scriptDirective, /'unsafe-inline'/);

console.log("Web XSS hardening tests: OK");
