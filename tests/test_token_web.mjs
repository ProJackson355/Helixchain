import assert from "node:assert/strict";
import { createHash, webcrypto } from "node:crypto";
import fs from "node:fs/promises";
import vm from "node:vm";

const html = await fs.readFile(new URL("../web_old/index.html", import.meta.url), "utf8");
const script = await fs.readFile(new URL("../web_old/app.js", import.meta.url), "utf8");
new vm.Script(script, { filename: "web_old/app.js" });

const canonicalSource = script.match(
  /function canonicalJson\(value\) \{[\s\S]*?\n\}(?=\n\nasync function signPayload)/,
)?.[0];
assert.ok(canonicalSource, "canonical token JSON helper is missing");
const canonicalJson = vm.runInNewContext(
  `(${canonicalSource.replace("function canonicalJson", "function")})`,
);
assert.equal(
  canonicalJson({ uri: "", symbol: "TST", amount: 5, name: "Tést" }),
  '{"amount":5,"name":"T\\u00e9st","symbol":"TST","uri":""}',
  "token signing bytes must match Python compact sorted JSON",
);

const exampleMetadata = JSON.parse(await fs.readFile(
  new URL("../web_old/token-metadata.example.json", import.meta.url), "utf8",
));
assert.deepEqual(exampleMetadata, {
  name: "Slop Coin",
  symbol: "SLOP",
  description: "A very sloppy coin",
  image: "https://lime-bizarre-bobcat-829.mypinata.cloud/ipfs/bafkreicamrjs54mnjxeycnb526aocbaickusaescglkbrme3kfgcwhcf2e",
});
assert.equal(
  createHash("sha256").update(canonicalJson(exampleMetadata)).digest("hex"),
  "499b0861500fc6f9a375a4e606a8a279e8f8cdb05aa8473642f8d4abac00efdd",
  "browser and node must commit the same metadata snapshot hash",
);

const addressSource = script.match(
  /async function tokenMintAddress\(creator, nonce\) \{[\s\S]*?\n\}(?=\n\nasync function signTransaction)/,
)?.[0];
assert.ok(addressSource, "deterministic token address helper is missing");
const context = {
  crypto: webcrypto,
  TextEncoder,
  _bytesToHex: bytes => Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join(""),
};
const tokenMintAddress = vm.runInNewContext(
  `(${addressSource.replace("async function tokenMintAddress", "async function")})`,
  context,
);
const creator = "a".repeat(40);
const nonce = "0123456789abcdef0123456789abcdef";
const mintAddress = await tokenMintAddress(creator, nonce);
const expectedMint = createHash("sha256")
  .update(`helix-token-mint:${creator}:${nonce}`)
  .digest("hex").slice(0, 40);
assert.equal(
  mintAddress,
  expectedMint,
  "browser and node must derive the same token addresses",
);

for (const id of [
  "panel-tokens", "dash-token-list", "token-list", "token-uri", "btn-token-load-metadata",
  "token-metadata-preview",
  "token-pane-wallet", "token-pane-discover", "token-pane-manage", "token-pane-create",
  "token-discovery-list", "token-search", "token-market-detail", "token-pool-controls",
  "token-pool-add-controls", "btn-token-add-pool-liquidity",
  "token-dad-address", "btn-token-create", "btn-token-transfer", "btn-token-mint",
  "token-new-dad", "btn-token-set-dad", "btn-token-revoke-dad",
  "send-asset", "send-amount-label",
]) {
  assert.match(html, new RegExp(`id="${id}"`), `${id} is missing`);
}

assert.match(
  script,
  /function heldTokens\(\)[\s\S]*?tokenBalanceUnits\(token\) > 0n/,
  "dashboard token discovery must be based on the wallet's confirmed balance",
);
assert.match(script, /function nativeTokenCardMarkup\(\)/);
assert.match(script, /data-native-asset="HLX"/);
assert.match(script, /function renderDashboardTokens\(\)[\s\S]*?nativeTokenCardMarkup\(\)/);
assert.match(script, /function renderTokens\(\)[\s\S]*?nativeTokenCardMarkup\(\)/);
assert.match(
  script,
  /function manageableTokens\(\)[\s\S]*?token\.dad_address === S\.address/,
  "DAD-controlled zero-balance tokens must remain available for management",
);
assert.match(
  script,
  /function renderDiscoveryTokens\(\)[\s\S]*?pool_hlx_reserve[\s\S]*?return leftLiquidity > rightLiquidity \? -1 : 1/,
  "token discovery must rank markets by locked HLX liquidity",
);
assert.match(script, /Liquidity: \$\{escapeHtml\(token\.pool_hlx_reserve \|\| 0\)\} HLX/);
for (const pane of ["wallet", "discover", "manage", "create"]) {
  assert.match(html, new RegExp(`data-token-pane="${pane}"`), `${pane} token tab is missing`);
}

const swapSource = script.match(
  /function swapQuote\(amountIn, reserveIn, reserveOut\) \{[\s\S]*?\n\}/,
)?.[0];
assert.ok(swapSource, "constant-product quote helper is missing");
const swapQuote = vm.runInNewContext(
  `(${swapSource.replace("function swapQuote", "function")})`,
);
assert.equal(swapQuote(2n, 7n, 500n), 110n);
assert.equal(swapQuote(100n, 390n, 9n), 1n);
for (const type of ["token_pool_create", "token_pool_add_hlx", "token_buy", "token_sell"]) {
  assert.match(script, new RegExp(`tx_type: ['\"]${type}['\"]|submitMarketTrade\\(['\"]${type}['\"]\\)`));
}
assert.match(script, /data-native-asset="HLX"/);
assert.match(script, /function renderNativeAsset\(\)/);
assert.match(script, /function tokenDistributionStats\(token\)/);
assert.match(script, /Supply distributed outside pool/);
assert.match(script, /logo-hex token-native-logo/);
assert.match(script, /9d7c721b209cee99a8158c524fa433ead9236781/);
assert.match(script, /DAD mint power/);
assert.match(script, /None - new HLX is mining-only/);
assert.match(script, /HLX_TOTAL_SUPPLY/);
assert.match(script, /NETWORK_STATS\.max_supply/);
assert.match(script, /Remaining mineable/);
assert.match(script, /Next block reward/);
assert.match(script, /native-supply-track/);
assert.match(script, /async function fetchTokenMetadataDocument\(rawUri\)/);
assert.match(script, /async function hydrateTokenMetadata\(token\)/);
assert.match(script, /token\.display_image = metadata\.image/);
assert.match(script, /token\.display_description = token\.description \|\| metadata\.description/);
assert.match(script, /await hydrateTokenCollection\(TOKENS\)/);
assert.match(script, /token\.display_image \|\| token\.image/);
assert.doesNotMatch(html, /id="token-pool-token-amount"/);
assert.match(script, /const amount = Number\(token\.balance \|\| 0\)/);
assert.match(script, /function renderTokenPriceChart\(container, token, rawPoints\)/);
assert.match(script, /TOKEN_CHART_RANGES[\s\S]*?minute[\s\S]*?hour[\s\S]*?day[\s\S]*?month/);
assert.match(script, /data-chart-range/);
assert.match(script, /id="token-chart-height"/);
assert.match(script, /id="token-chart-width"/);
assert.match(script, /data-chart-zoom/);
assert.match(script, /addEventListener\('wheel'[^]*?passive: false/);
assert.match(script, /function buildChartCandles\(points, startSeconds, endSeconds\)/);
assert.match(script, /class="chart-candle \${direction}/);
assert.match(html, /\.chart-candle\.bearish \.candle-body \{ fill:var\(--red\)/);
assert.match(html, /\.chart-candle\.bullish \.candle-body \{ fill:var\(--green\)/);
assert.match(html, /\.chart-scroll \{[^}]*overflow-x:auto/);
assert.match(script, /function tokenSwapQuote\(source, target, amount\)/);
assert.match(script, /tx_type: 'token_swap'/);
assert.match(script, /target_mint_address: target\.mint_address/);
assert.match(script, /const trend = change > 0 \? 'bullish' : change < 0 \? 'bearish' : 'neutral'/);
assert.match(html, /price-chart-card\.bullish \.chart-line \{ stroke:var\(--green\)/);
assert.match(html, /price-chart-card\.bearish \.chart-line \{ stroke:var\(--red\)/);
assert.match(script, /\/market\/history/);
assert.match(script, /id="token-price-chart"/);
assert.match(script, /function openTokenMarket\(mintAddress\)/);
assert.match(script, /tx_type: 'token_transfer'[\s\S]*?mint_address: token\.mint_address/);
assert.match(script, /function renderSendAssets\(\)/);

console.log("Custom token web_old contract: OK");
