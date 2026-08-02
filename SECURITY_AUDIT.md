# Helix Security Audit

_Scope: the web wallet (`web/`) and the blockchain node (`node/`). Date: 2026-07-29._

This audit reviewed the Cloudflare Worker gateway, security headers/CSP, the browser
wallet (XSS and key handling), the node HTTP API, the security middleware, the
consensus rules (signatures, transaction/block validation, reward and supply
invariants, NFT rules), and the P2P layer. Overall the codebase is well hardened;
one higher-severity issue was found and fixed, and a few recommendations remain.

## Summary of findings

| # | Severity | Area | Status |
|---|----------|------|--------|
| 1 | High | Consensus — signature malleability replay window on the reset chain | **Fixed** |
| 2 | Medium | P2P — SSRF via unvalidated peer URLs | Open (recommendation) |
| 3 | Low | Config — relaunch left fee/envelope/state-commitment heights at old defaults | Open (decision) |
| 4 | Info | Rate limiting through the Worker needs an admin key to be per-client | By design |
| 5 | Info | `img-src https:` allows arbitrary remote token/NFT images | Accepted |

---

## Finding 1 — Signature-malleability replay window (High) — FIXED

**What.** ECDSA signatures are malleable: for any valid signature `(r, s)` the
variant `(r, n − s)` is also valid for the same message. Because a transaction id
is `sha256(data + signature)`, a malleated signature yields a *different* txid for
the *same* transfer. The node normally defends against this by (a) requiring
canonical low-S signatures and (b) de-duplicating by a signature-independent
"canonical id". Both defenses are gated on `canonical_signature_activation_height`,
which **defaults to 200** and was not overridden when the chain was relaunched from
a fresh genesis with "all rules at block 1".

**Impact.** For blocks 1–199 of the reset chain, block validation skipped both the
low-S requirement and the canonical-duplicate check (`node/blockchain.py`, the
`block.index >= self.canonical_signature_activation_height` guards). The mempool
rejects non-canonical signatures unconditionally, but a miner assembling a block
directly (via `/mining/submit` or a gossiped block) bypasses the mempool. A payment
recipient could therefore take a confirmed transfer, flip its `s` value, and replay
it under a new txid — double-executing the transfer and draining the sender up to
their balance. Only same-chain replay; requires producing a block.

**Fix applied.** Set `canonical_signature_activation_height: 1` in `config.json`.
This is safe because every legitimate signer already emits canonical low-S:
`Transaction.sign()` normalises via `canonical_signature_hex()`, and the browser
wallet signs with noble-secp256k1 (low-S by default). Verified: normal wallet-style
signatures pass, a malleated high-S variant is now flagged non-canonical, and the
full test suite still passes. Apply on a young chain (or another reset) so no block
below the old height 200 exists.

---

## Finding 2 — SSRF via unvalidated peer URLs (Medium) — recommendation

**What.** `normalize_peer()` (`node/peer_manager.py`) accepts any `http(s)` URL and
only checks the scheme and that a hostname exists. It does not reject loopback,
private (RFC1918), link-local (`169.254.169.254` — the cloud metadata endpoint), or
other reserved addresses. When a peer URL reaches the node's peer list, the node
issues background GET requests to it during sync/discovery.

**Impact.** Blind server-side request forgery: an attacker who can get a URL into a
node's peer set can make the node probe internal services or the cloud metadata
endpoint. It is *blind* (responses are parsed as chain JSON and discarded, not
reflected to the attacker), which limits exfiltration, but it still enables internal
port/host probing and hitting unauthenticated internal endpoints. Reachability
depends on how peers are added: `/nodes/register` is admin-gated, but public
submission/gossip paths can feed peers on a keyless node.

**Recommendation.** In `normalize_peer` (or before adding/fetching a peer), resolve
the host and reject `is_loopback`, `is_link_local`, `is_reserved`, `is_multicast`,
and (outside an explicit local-testing allowlist) `is_private` addresses. Keep a
config switch so localhost peers still work for development. Also confirm all
outbound peer requests use the configured `request_timeout`. I can implement this on
request.

---

## Finding 3 — Relaunch config left other activation heights at old defaults (Low)

`transaction_fee_activation_height` (200), `transaction_envelope_activation_height`
(1000) and `state_commitment_activation_height` (inherits 1000) were not set for the
block-1 relaunch, so they remain inconsistent with the "all rules from block 1"
intent:

- **Fees** don't engage until block 200, yet the wallet shows a "1 HLX network fee".
  Cosmetic/economic, not a security issue.
- **Envelope** (per-account `sequence` and `chain_id`) and **state-commitment**
  (per-block state root) don't engage until block 1000. The `chain_id` field is the
  cross-chain replay defense and `sequence` gives account ordering; state
  commitments let light clients verify state.

Security impact is limited now that Finding 1 closes same-chain replay. Enabling the
envelope at block 1 is **not** a drop-in change: the browser wallet does not yet emit
`chain_id`/`sequence`, so turning it on would reject all wallet transactions. Decide
the intended heights; enabling the envelope needs a matching wallet update first. I
did not auto-change these to avoid breaking sends.

---

## Finding 4 — Worker rate limiting needs an admin key to be per-client (Info)

A same-host `cloudflared` tunnel delivers every visitor from loopback. The node only
trusts the Worker's `x-helix-client-ip` header when a valid admin key is present
(guarded by a constant-time compare). Without `HELIX_ADMIN_API_KEY`, all
Worker-proxied traffic is treated as loopback — never banned and sharing one
rate-limit bucket. This is a deliberate anti-spoofing trade-off (documented in
`security.py`). For a public node, set `HELIX_ADMIN_API_KEY` so per-client rate
limiting and bans function.

---

## Finding 5 — Remote images allowed by CSP (Info, accepted)

`img-src 'self' data: https:` lets token/NFT images load from any HTTPS origin, by
design. No script execution is possible (`script-src 'self'`, `script-src-attr
'none'`), but user-supplied image URLs can act as logging beacons (IP/user-agent) or
render broken/spoofed art. Acceptable for an educational wallet; a future option is
to proxy or hash-pin images.

---

## What is done well (verified strengths)

**Web gateway (`web/_worker.js`).** Strict method+regex route allowlist; admin routes
gated behind `HELIX_ENABLE_ADMIN_API`; request-body cap (declared and actual);
strips client-supplied `authorization`, `cookie`, `cf-*`, `x-forwarded-*`,
`x-helix-api-key`, `x-helix-client-ip` before forwarding (prevents admin-key and
client-IP spoofing); upstream target is operator config, not user input (no
user-controlled SSRF); `redirect: manual`; only content-type/cache-control passed
back.

**Security headers / CSP.** Both the Cloudflare `_headers` file and the node's
`WebSecurityHeadersMiddleware` serve `script-src 'self'` with no `unsafe-inline` and
`script-src-attr 'none'` — a strong XSS backstop even if markup is injected — plus
`object-src 'none'`, `base-uri 'none'`, `frame-ancestors 'none'`, HSTS, nosniff,
COOP/CORP, and a locked-down `Permissions-Policy`.

**Browser wallet.** Chain-derived strings (token/NFT names, descriptions, images,
addresses) are consistently passed through `escapeHtml`; `toast`/`setAlert` use
`textContent`; `transactionDetailRow` escapes by default and its one `rawHtml` use is
a trusted, code-built badge. Private keys live only in the browser, AES-GCM encrypted
with PBKDF2 (600k iterations); signing is client-side; keys are never transmitted.

**Consensus (`node/blockchain.py`, `node/transaction.py`).** Sender address is bound
to the supplied public key before ECDSA/SHA-256 verification; signatures are
normalised to canonical low-S on signing; reward amount and reward-id are recomputed
and checked; total supply is capped; block timestamps are bounded (parent tolerance
+ near-future cap); difficulty retargeting is deterministic; NFT ownership/mint rules
reject forged ids, tampered metadata, and unauthorized transfers.

**Node API & middleware (`node/node.py`, `node/security.py`).** Strict per-type field
whitelisting in `_transaction_from_payload`; `validate_hex`/`safe_identifier` on
inputs; filename allowlists for icons/downloads (no path traversal); dual body-size
enforcement (header + streamed); IP bans with loopback exemption; per-group sliding
rate limits; constant-time (`hmac.compare_digest`) admin-key check; CORS limited to
configured origins.

---

## Actions

- **Done:** `canonical_signature_activation_height: 1` (Finding 1); full node test
  suite re-run — 94 passed (GUI-only test files require `tkinter`, absent in the
  audit sandbox; unrelated to this change).
- **Recommended next:** peer-URL SSRF screening (Finding 2); decide fee/envelope/
  state-commitment heights and, if enabling the envelope, add `chain_id`/`sequence`
  to the wallet (Finding 3); set an admin key on any public node (Finding 4).

_Educational software — not professionally audited beyond this review, and not
intended as production financial infrastructure._
