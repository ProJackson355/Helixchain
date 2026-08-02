import assert from "node:assert/strict";
import fs from "node:fs/promises";

const bundleUrl = new URL("../web/secp256k1.js", import.meta.url);
const source = await fs.readFile(bundleUrl, "utf8");
assert.doesNotMatch(source, /https?:\/\//, "signing bundle must not load remote code");

const { secp256k1 } = await import(bundleUrl.href);
const privateKey = new Uint8Array(32);
privateKey[31] = 1;
const message = new TextEncoder().encode("helix security audit");
const signature = secp256k1.sign(message, privateKey, { format: "der" });
const publicKey = secp256k1.getPublicKey(privateKey, true);
assert.equal(
  secp256k1.verify(signature, message, publicKey, { format: "der" }),
  true,
);

function derScalars(bytes) {
  assert.equal(bytes[0], 0x30);
  let offset = 2;
  assert.equal(bytes[offset++], 0x02);
  const rLength = bytes[offset++];
  const r = BigInt(`0x${Buffer.from(bytes.slice(offset, offset + rLength)).toString("hex")}`);
  offset += rLength;
  assert.equal(bytes[offset++], 0x02);
  const sLength = bytes[offset++];
  const s = BigInt(`0x${Buffer.from(bytes.slice(offset, offset + sLength)).toString("hex")}`);
  return { r, s };
}

const order = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141n;
const { r, s } = derScalars(signature);
assert.ok(r > 0n && r < order);
assert.ok(s > 0n && s <= order / 2n, "browser signatures must use low-S form");

console.log("Self-hosted secp256k1 signing bundle: OK");
