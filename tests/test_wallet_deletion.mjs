import assert from "node:assert/strict";
import fs from "node:fs/promises";
import vm from "node:vm";

const html = await fs.readFile(new URL("../web_old/index.html", import.meta.url), "utf8");
const script = await fs.readFile(new URL("../web_old/app.js", import.meta.url), "utf8");
assert.match(html, /id="btn-delete-wallet"/, "delete-wallet button is missing");
assert.match(html, /id="delete-wallet-alert"/, "delete-wallet feedback area is missing");

const loadStore = script.match(/function _loadStore\(\) \{[\s\S]*?\n\}/)?.[0];
const saveStore = script.match(/function _saveStore\(store\) \{[\s\S]*?\n\}/)?.[0];
const deleteRecord = script.match(/function deleteWalletRecord\(name\) \{[\s\S]*?\n\}/)?.[0];
assert.ok(loadStore && saveStore && deleteRecord, "local wallet deletion helpers are missing");

const storage = new Map([
  ["hlx_wallets_v1", JSON.stringify({ alice: { address: "a" }, bob: { address: "b" } })],
]);
const context = {
  localStorage: {
    getItem: key => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, value),
  },
};
const deleteWalletRecord = vm.runInNewContext(
  `(() => {
    const WALLET_STORE_KEY = 'hlx_wallets_v1';
    ${loadStore}
    ${saveStore}
    ${deleteRecord}
    return deleteWalletRecord;
  })()`,
  context,
);

assert.equal(deleteWalletRecord("alice"), true);
assert.deepEqual(JSON.parse(storage.get("hlx_wallets_v1")), { bob: { address: "b" } });
assert.equal(deleteWalletRecord("missing"), false);
assert.deepEqual(JSON.parse(storage.get("hlx_wallets_v1")), { bob: { address: "b" } });

const handlerStart = script.indexOf("document.getElementById('btn-delete-wallet')");
const handlerEnd = script.indexOf("// ============================================================", handlerStart);
const handler = script.slice(handlerStart, handlerEnd);
assert.ok(handler.includes("await loadWallet(walletName, password)"), "password verification is required");
assert.ok(handler.includes("window.confirm("), "destructive confirmation is required");
assert.ok(
  handler.indexOf("await loadWallet(walletName, password)") < handler.indexOf("deleteWalletRecord(walletName)"),
  "the wallet must be verified before deletion",
);
assert.ok(
  handler.indexOf("window.confirm(") < handler.indexOf("deleteWalletRecord(walletName)"),
  "confirmation must happen before deletion",
);

console.log("Local wallet deletion tests: OK");
