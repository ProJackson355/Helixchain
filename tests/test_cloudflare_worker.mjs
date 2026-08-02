import assert from "node:assert/strict";
import fs from "node:fs/promises";

const source = await fs.readFile(new URL("../web/_worker.js", import.meta.url), "utf8");
const worker = (await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`)).default;

const assets = {
  fetch() {
    throw new Error("asset binding should not handle API tests");
  },
};

const originalFetch = globalThis.fetch;
let defaultForwarded;
globalThis.fetch = async url => {
  defaultForwarded = String(url);
  return new Response(JSON.stringify({ status: "ok" }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
};
let response = await worker.fetch(
  new Request("https://wallet.pages.dev/api/health"),
  { ASSETS: assets },
);
assert.equal(response.status, 200);
assert.equal(defaultForwarded, "https://node.hlxchain.com/health");
globalThis.fetch = originalFetch;

response = await worker.fetch(
  new Request("https://wallet.pages.dev/api/chain/full"),
  { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
);
assert.equal(response.status, 404);

response = await worker.fetch(
  new Request("https://wallet.pages.dev/api/health"),
  { ASSETS: assets, HELIX_NODE_URL: '["https://node.example"' },
);
assert.equal(response.status, 503);

response = await worker.fetch(
  new Request("https://wallet.pages.dev/api/health"),
  { ASSETS: assets, HELIX_NODE_URL: "http://node.example" },
);
assert.equal(response.status, 503);
assert.match(await response.text(), /must use HTTPS/);

response = await worker.fetch(
  new Request("https://wallet.pages.dev/api/mine?address=" + "a".repeat(40), { method: "POST" }),
  { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
);
assert.equal(response.status, 404);

let forwarded;
globalThis.fetch = async (url, init) => {
  forwarded = { url: String(url), init };
  return new Response(JSON.stringify({ status: "ok" }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
};

try {
  response = await worker.fetch(
    new Request("https://wallet.pages.dev/api/health?probe=1", {
      headers: {
        "cf-connecting-ip": "198.51.100.25",
        cookie: "session=private",
        authorization: "Bearer private",
        referer: "https://private.example/account",
        "cf-access-jwt-assertion": "private-jwt",
      },
    }),
    {
      ASSETS: assets,
      HELIX_NODE_URL: "https://node.example/base/",
      HELIX_ADMIN_API_KEY: "test-secret",
    },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, "https://node.example/base/health?probe=1");
  assert.equal(forwarded.init.headers.get("x-helix-api-key"), "test-secret");
  assert.equal(forwarded.init.headers.get("x-helix-client-ip"), "198.51.100.25");
  assert.equal(forwarded.init.headers.get("cookie"), null);
  assert.equal(forwarded.init.headers.get("authorization"), null);
  assert.equal(forwarded.init.headers.get("referer"), null);
  assert.equal(forwarded.init.headers.get("cf-access-jwt-assertion"), null);
  assert.equal(response.headers.get("cache-control"), "no-store");

  const holder = "a".repeat(40);
  response = await worker.fetch(
    new Request(`https://wallet.pages.dev/api/transaction/envelope/${holder}`),
    { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, `https://node.example/transaction/envelope/${holder}`);

  response = await worker.fetch(
    new Request(`https://wallet.pages.dev/api/tokens?holder=${holder}`),
    { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, `https://node.example/tokens?holder=${holder}`);

  const mint = "b".repeat(40);
  response = await worker.fetch(
    new Request(`https://wallet.pages.dev/api/token/${mint}`),
    { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, `https://node.example/token/${mint}`);

  response = await worker.fetch(
    new Request(`https://wallet.pages.dev/api/token/${mint}/market/history`),
    { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, `https://node.example/token/${mint}/market/history`);

  const nft = "d".repeat(40);
  response = await worker.fetch(
    new Request(`https://wallet.pages.dev/api/nft/${nft}/market/history`),
    { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, `https://node.example/nft/${nft}/market/history`);

  const dad = "c".repeat(40);
  response = await worker.fetch(
    new Request(`https://wallet.pages.dev/api/dad/${dad}/tokens`),
    { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, `https://node.example/dad/${dad}/tokens`);

  response = await worker.fetch(
    new Request("https://wallet.pages.dev/api/transactions/recent?limit=25"),
    { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, "https://node.example/transactions/recent?limit=25");

  const cancelId = "e".repeat(64);
  response = await worker.fetch(
    new Request(`https://wallet.pages.dev/api/transaction/${cancelId}/cancel`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ sender: holder }),
    }),
    { ASSETS: assets, HELIX_NODE_URL: "https://node.example" },
  );
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, `https://node.example/transaction/${cancelId}/cancel`);

  const failoverCalls = [];
  globalThis.fetch = async (url) => {
    failoverCalls.push(String(url));
    if (String(url).startsWith("https://node-one.example")) {
      throw new Error("node one offline");
    }
    return new Response(JSON.stringify({ chain: [] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };
  response = await worker.fetch(
    new Request("https://wallet.pages.dev/api/chain"),
    {
      ASSETS: assets,
      HELIX_NODE_URL: JSON.stringify([
        "https://node-one.example",
        "https://node-two.example/base/",
      ]),
    },
  );
  assert.equal(response.status, 200);
  assert.deepEqual(failoverCalls, [
    "https://node-one.example/chain",
    "https://node-two.example/base/chain",
  ]);

  const adminCalls = [];
  globalThis.fetch = async url => {
    adminCalls.push(String(url));
    if (String(url).endsWith("/health")) {
      return new Response("", {
        status: String(url).startsWith("https://node-one.example") ? 530 : 200,
      });
    }
    throw new Error("uncertain administrative response");
  };
  response = await worker.fetch(
    new Request("https://wallet.pages.dev/api/nodes/sync_now", { method: "POST" }),
    {
      ASSETS: assets,
      HELIX_NODE_URL: ["https://node-one.example", "https://node-two.example"],
      HELIX_ENABLE_ADMIN_API: "true",
    },
  );
  assert.equal(response.status, 502);
  assert.deepEqual(adminCalls, [
    "https://node-one.example/health",
    "https://node-two.example/health",
    "https://node-two.example/nodes/sync_now",
  ]);

  adminCalls.length = 0;
  const jobId = "d".repeat(32);
  for (const request of [
    new Request(`https://wallet.pages.dev/api/mine?address=${holder}`, { method: "POST" }),
    new Request(`https://wallet.pages.dev/api/mine/start?address=${holder}`, { method: "POST" }),
    new Request(`https://wallet.pages.dev/api/mine/status/${jobId}`),
  ]) {
    response = await worker.fetch(request, {
      ASSETS: assets,
      HELIX_NODE_URL: ["https://node-one.example", "https://node-two.example"],
      HELIX_ENABLE_ADMIN_API: "true",
    });
    assert.equal(response.status, 404);
  }
  assert.deepEqual(adminCalls, []);
} finally {
  globalThis.fetch = originalFetch;
}

console.log("Cloudflare Worker gateway tests: OK");
