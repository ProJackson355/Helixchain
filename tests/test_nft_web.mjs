import assert from "node:assert/strict";
import fs from "node:fs/promises";

const html = await fs.readFile(new URL("../web/index.html", import.meta.url), "utf8");
const script = await fs.readFile(new URL("../web/app.js", import.meta.url), "utf8");

assert.match(html, /data-nft-pane="wallet"[^>]*>My NFTs/);
assert.match(html, /data-nft-pane="manage"[^>]*>Manage NFTs/);
assert.match(html, /data-nft-pane="discover"[^>]*>Discover/);
assert.match(html, /data-nft-pane="create"[^>]*>Create NFT/);
assert.match(html, /id="nft-discovery-gallery"/);
assert.match(html, /id="nft-manage-gallery"/);
assert.match(html, /id="nft-search"/);
assert.match(script, /api\('GET', '\/nfts\?limit=500'\)/);
assert.match(script, /function renderDiscoveredNfts\(\)/);
assert.match(script, /closest\?\.\('\.nft-tab\[data-nft-pane\]'\)/);
assert.match(script, /if \(pane === 'discover'\) loadDiscoverNfts\(\)/);
assert.match(script, /if \(pane === 'manage'\) loadManageNfts\(\)/);
assert.match(script, /pane\.hidden = !active/);
for (const action of [
  "nft_list", "nft_cancel_listing", "nft_bid", "nft_cancel_bid",
  "nft_accept_bid", "nft_buy", "nft_set_royalty",
]) {
  assert.match(script, new RegExp(`signedNftAction\\(\\s*'${action}'`));
}
assert.match(script, /signPayload\(S\.privateKey, payload\)/);
assert.match(script, /highest escrow-backed bid/);
assert.match(script, /last confirmed sale/);
assert.match(script, /data-nft-save-listing/);
assert.match(script, /All bids/);
assert.match(script, /Number\(right\.amount\) - Number\(left\.amount\)/);
assert.match(script, /royalty_bps: royaltyBps/);
assert.match(script, /data-nft-details/);
assert.match(script, /function openNftDetails\(nftId\)/);
assert.match(script, /\/nft\/\$\{encodeURIComponent\(nft\.nft_id\)\}\/market\/history/);
assert.match(script, /__nft: true/);
assert.match(html, /id="nft-modal"/);
assert.match(script, /id="nft-price-chart/);

console.log("NFT discovery, management, and marketplace web tests: OK");
