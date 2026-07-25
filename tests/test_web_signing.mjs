import assert from "node:assert/strict";
import fs from "node:fs/promises";
import vm from "node:vm";

const html = await fs.readFile(new URL("../web/index.html", import.meta.url), "utf8");
const script = await fs.readFile(new URL("../web/app.js", import.meta.url), "utf8");
const match = script.match(
  /function transactionPayload\(sender, receiver, amount\) \{[\s\S]*?\n\}/,
);
assert.ok(match, "transactionPayload helper is missing from the web wallet");

const transactionPayload = vm.runInNewContext(
  `(${match[0].replace("function transactionPayload", "function")})`,
);

const sender = "a".repeat(40);
const receiver = "b".repeat(40);
const payload = transactionPayload(sender, receiver, "12");

assert.equal(
  payload,
  `{"amount":12,"receiver":"${receiver}","sender":"${sender}"}`,
  "browser signing bytes must match Python's compact, sorted transaction JSON",
);

console.log("Web transaction signing contract: OK");
