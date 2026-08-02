# Helixchain Security Audit — 2026-07-27

## Executive summary

This review covered the Helix consensus implementation, asset authorization,
transaction signing and replay handling, NFT and fungible-token state changes,
mempool cancellation, node/admin routes, peer inputs, the Cloudflare Pages
gateway, browser key storage, DOM rendering, and the deployed wallet at
`https://wallet.hlxchain.com/`.

One critical cryptographic replay issue, one high-severity web supply-chain
risk, two medium-severity gateway/admin weaknesses, and browser-header
hardening gaps were confirmed and fixed in the project. The fixes use peer
protocol 14. Canonical signatures activate at block 200 so blocks already on
the chain remain valid. Every node must be upgraded and restarted before block
200. No chain reset is required.

The production website does not receive these source changes automatically.
At audit time it was still serving the earlier `app.js?v=20260736` build and
must be redeployed from the updated `web` directory.

Security cannot be proven absolutely by one review. The residual-risk section
lists architectural risks and operational controls that remain important.

## Scope and methods

- Manual trust-boundary and data-flow review of `node/`, `wallet/`, the miner
  interfaces, `web/app.js`, `web/_worker.js`, service-worker behavior, and
  security configuration.
- Adversarial review of sender/public-key binding, all signed transaction
  fields, transaction IDs, duplicate detection, DAD checks, NFT ownership,
  listing and bid escrow, royalty control, fees, reward validation, supply cap,
  chain replacement, checkpoints, request limits, admin authentication, CORS,
  and browser rendering sinks.
- Non-destructive production checks of TLS redirect behavior, response headers,
  public gateway allowlisting, private-route rejection, application runtime,
  console warnings, API connectivity, and reflected-XSS handling.
- `pip-audit` against current Python requirements: no known vulnerabilities.
- Bandit scan of 5,022 lines in `node/` and `wallet/`: no medium- or
  high-severity findings. Eleven low-severity notices were broad exception
  handlers or false positives on numeric configuration values.
- Full automated regression suite: 52 Python tests and 12 JavaScript tests.
- Replay validation of a temporary copy of the real height-163 chain under the
  upgraded rules: valid, with no modification to the live database.

## Confirmed findings and remediation

### HLC-001 — Critical — ECDSA signature malleability could replay transfers

ECDSA permits `(r, s)` and `(r, n-s)` as mathematically valid signatures for
the same message. Helix previously included the signature bytes in the
transaction ID but accepted both forms. An attacker observing a signed
transaction could therefore transform its signature without the private key,
obtain a different transaction ID, and bypass transaction-ID duplicate checks.
Repeatable HLX and fungible-token operations could execute again if the sender
still had sufficient balance.

Remediation:

- Python wallet signing now always emits canonical low-S DER signatures.
- New mempool transactions and cancellation proofs reject high-S signatures.
- Consensus requires canonical low-S signatures from block 200.
- Nodes calculate and index a signature-equivalent canonical ID. The high-S and
  low-S forms are treated as the same transaction, including when the original
  appeared before activation.
- An adversarial regression test constructs the valid high-S twin without the
  private key, proves that ordinary ECDSA verification accepts it, and proves
  Helix rejects it.

Status: fixed in protocol 14; deploy all nodes before block 200.

### HLC-002 — High — Runtime CDN controlled wallet signing code

The deployed wallet dynamically imported Noble Curves from `esm.sh`. Code from
that response ran in the wallet page and implemented transaction signing. A
compromise of the CDN path or upstream delivery could have exposed an unlocked
private key or changed transaction details before signing.

Remediation:

- Noble Curves 2.2.0 is pinned and bundled into `web/secp256k1.js`.
- The browser loads the signing implementation only from its own origin.
- CSP `script-src` is now exactly `'self'`; remote executable code is not
  permitted.
- A test imports the bundled implementation, signs and verifies data, and
  verifies the emitted DER signature is low-S.
- Bundled file SHA-256:
  `3b169d3d803a8301844d1ce188f8d4e4df674363fc30cd77c0d133e54225bfd8`.

Status: fixed in source; redeploy the `web` directory.

### HLC-003 — Medium — Plaintext node targets could expose gateway secrets

The Pages Worker accepted Internet-facing `http://` node URLs. When an admin
key was configured, it could be transmitted without transport encryption.

Remediation: production node targets must use HTTPS. Plain HTTP remains allowed
only for loopback (`localhost`, `127.0.0.1`, or `::1`) during local Wrangler
development.

Status: fixed in source; redeploy the `web` directory.

### HLC-004 — Medium — Browser credentials could be forwarded to a node

The gateway rebuilt upstream headers but did not explicitly remove cookies,
Authorization values, Cloudflare Access assertions, or the referring page.
This mattered if authentication was later added to the Pages domain or if a
browser extension supplied those headers.

Remediation: the Worker strips `Cookie`, `Authorization`,
`Proxy-Authorization`, `Referer`, and `CF-Access-Jwt-Assertion`, in addition to
the existing proxy and Helix-key headers, before adding only the configured
node key and validated client IP.

Status: fixed in source; redeploy the `web` directory.

### HLC-005 — Medium — Admin protection omitted sensitive routes and could fail open

`/nodes/register` and `/security/status` were not present in the configured
admin route list. Also, if a config file omitted the list entirely, enabling
admin authentication did not protect a built-in fallback set of routes. A
public caller could poison the peer registry or read security state despite an
operator believing admin protection was enabled.

Remediation: both routes are protected, and the middleware has a built-in
fail-closed admin route set when configuration is incomplete. Tests verify a
missing route list still returns HTTP 401 for node registration.

Status: fixed. Operators exposing a node publicly should set
`HELIX_REQUIRE_ADMIN_API_KEY=true` and a strong, stable
`HELIX_ADMIN_API_KEY`.

### HLC-006 — Low — Missing transport/isolation headers and unprotected local UI

The production page had CSP, anti-framing, MIME-sniffing, permissions, and
referrer controls, but no HSTS or cross-origin isolation headers. The same UI
served directly by a Helix node did not receive the Pages `_headers` policy.

Remediation:

- Pages adds one-year HSTS with subdomains/preload, COOP `same-origin`, and
  CORP `same-origin`.
- Node-served static wallet assets receive matching CSP, anti-framing,
  MIME-sniffing, referrer, permissions, COOP, and CORP controls.
- API responses intentionally do not receive static-asset CORP, preserving
  legitimate API access governed by CORS.

Status: fixed in source. Submit the domain to the browser HSTS preload list only
after confirming every subdomain will remain HTTPS permanently.

## Authorization and asset-theft conclusions

- A transaction sender is derived from SHA-256 of the compressed secp256k1
  public key and must equal the signed sender address.
- Sender, receiver, amount, fee, chain ID, account sequence, expiry height,
  operation type, token/NFT identifier, nonce,
  DAD changes, pool inputs, slippage limits, NFT metadata, and royalty changes
  are covered by canonical signed JSON where relevant. Parser contract tests
  cover every supported transaction type.
- Altering a receiver, amount, asset identifier, fee, authority, royalty, or
  marketplace field invalidates the signature.
- HLX cannot be spent without the sender key and sufficient confirmed balance.
- Fungible tokens cannot be transferred without the holder key. Minting,
  burning, pool creation, direct liquidity addition, and authority changes
  require the current signed DAD authority.
- NFTs cannot be transferred, listed, delisted, or sold without the current
  owner key. Bid funds are escrowed in consensus. Royalty changes require the
  creator key and are permanently locked after the first ownership change.
- Mining rewards must be the final and only SYSTEM transaction, use the exact
  reward ID and amount, and respect the native supply cap.
- Public address, history, transaction, token, NFT, and chain endpoints expose
  public blockchain data by design; they do not authorize writes. Asset writes
  are controlled by signatures and consensus rather than a user-supplied URL
  identifier, so classic IDOR does not grant ownership.

## Production website observations

At the time of review:

- HTTP redirected to HTTPS with status 301.
- The page returned CSP, `X-Frame-Options: DENY`, `nosniff`, no-referrer, and a
  restrictive permissions policy. Inline scripts and inline script attributes
  were absent.
- `/api/health` was reachable. `/api/chain/full` and
  `/api/security/status` were blocked by the gateway allowlist with 404.
- A payment-link reflected-XSS probe was safely reduced to a validated address
  description; the injected string did not appear as executable markup.
- The page connected to the node and produced no browser console warnings or
  errors during the logged-out check.
- Cloudflare Pages Analytics injected a
  `static.cloudflareinsights.com/beacon.min.js` tag. The current CSP does not
  authorize that origin, so it should be blocked. Disable Pages Web Analytics
  injection for a cleaner, auditable wallet page; do not weaken CSP to permit
  it.
- The live page did not yet have HSTS and still referenced the remote signing
  import in its deployed `app.js`. Redeployment is required.

## Residual risks and operational requirements

1. **Cancellation is final only after its replacement confirms.** Protocol 15
   adds chain-bound account sequences, expiry heights, higher-fee replacement,
   and a signed on-chain cancellation transaction. Before block 1000, legacy
   cancellation tombstones remain best-effort. At and after block 1000, a
   confirmed cancellation consumes the sequence permanently; before it confirms,
   a miner can still choose the original same-sequence transaction, as with
   replace-by-fee systems generally. Cancellation is not key rotation.
2. **Unlocked browser sessions contain key material.** To survive refresh for
   one hour, the tab's session storage contains the unlocked private scalar.
   The self-only CSP materially reduces script injection risk, but a malicious
   browser extension, compromised device, or compromised same-origin deployment
   can still steal it. Use a dedicated browser profile/device for meaningful
   value and lock the wallet when finished.
3. **Educational implementation.** This is not a substitute for an independent
   professional audit, formal verification, hardware-wallet support, a bug
   bounty, or production incident monitoring. Do not market it as theft-proof.
4. **Consensus majority risk.** Proof of work cannot prevent a sufficiently
   powerful miner coalition from reorganizing uncheckpointed history or
   censoring transactions. Wait for multiple confirmations for valuable sales.
5. **Token impersonation and metadata privacy.** Names, symbols, and artwork are
   not unique. Users must verify MNT/NFT identifiers and DAD authority. Remote
   HTTPS images and metadata can observe viewer IP addresses; use trusted
   content gateways.
6. **Admin authentication remains opt-in.** Public production nodes should
   enable the admin key, keep it out of source control, expose the node only
   through TLS/tunnel controls, firewall direct access, rotate a disclosed key,
   and monitor rate-limit/security logs.
7. **Cloudflare account trust.** Pages and Workers serve the wallet code. An
   account takeover can replace that code despite CSP. Require phishing-resistant
   MFA, least-privilege Cloudflare access, deployment review, and account alerts.

## Deployment order

1. Stop mining before block 200 until every node operator has protocol 14.
2. Back up `database_8000.json`, wallet files, configuration, and the stable
   admin key.
3. Deploy protocol 14 to every node and restart each process. Do not reset the
   chain.
4. Confirm peers report protocol 14 and the copied/current chain validates.
5. Upload the complete updated `web` directory to Cloudflare Pages.
6. Confirm the live CSP says `script-src 'self'`, HSTS is present,
   `/secp256k1.js?v=2.2.0` returns 200, and `app.js` contains no `esm.sh` import.
7. Disable Cloudflare Pages Web Analytics script injection unless it can be
   operated without adding third-party executable code to the wallet page.

## Verification results

- Python unit/security tests: 52 passed.
- JavaScript gateway/UI/security tests: 12 passed.
- Python dependency advisories: zero known vulnerabilities.
- Bandit: zero medium/high findings; 11 low notices reviewed.
- Existing chain-copy replay: height 163 valid under protocol 14.
- `git diff --check`: required before release packaging.
