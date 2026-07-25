import assert from "node:assert/strict";
import fs from "node:fs/promises";

const html = await fs.readFile(new URL("../web/index.html", import.meta.url), "utf8");
const script = await fs.readFile(new URL("../web/app.js", import.meta.url), "utf8");

assert.match(
  html,
  /<input id="login-name" type="text"[^>]*autocomplete="username"/,
  "wallet name login must be a typed username field",
);
assert.doesNotMatch(
  html,
  /<select id="login-name"/,
  "wallet name login must not be a dropdown",
);
assert.match(
  script,
  /document\.getElementById\('login-name'\)\.value\.trim\(\)/,
  "login must read the typed wallet name",
);
assert.match(
  script,
  /\['login-name', 'login-pass'\][\s\S]*?if \(e\.key === 'Enter'\) doLogin\(\)/,
  "pressing Enter in either login field must unlock the wallet",
);

console.log("Typed wallet-name login tests: OK");
