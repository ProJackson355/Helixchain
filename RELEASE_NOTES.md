# Helix 1.0.0 — Token Discovery and Exchange

## Protocol 10 difficulty reset and token swaps

- Reset difficulty to 3 once at block 161 without changing historical blocks.
- Keep difficulty at 3 through block 170, then resume deterministic adjustment
  every 10 blocks beginning at block 171.
- Use a 160-second target after block 161: averages below 80 seconds raise
  difficulty by one and averages above 160 seconds lower it by one.
- Add atomic `token_swap` transactions routed through both tokens' HLX pools,
  activating at block 200 under peer protocol 10.
- Add timestamp-accurate interactive charts and per-round miner timing logs.

## Token protocol

- Added on-chain `token_create`, `token_mint`, `token_transfer`, and `token_set_authority` transactions.
- Added on-chain `token_pool_create`, `token_pool_add_hlx`, `token_buy`, `token_sell`, and `token_swap`
  transactions with constant-product pricing, a 0.3% pool fee, and signed
  minimum-output protection.
- Added deterministic MNT identifiers, explicit DAD management authorities, decimals, metadata URI, and Solana-style zero-supply mint creation.
- DAD authority can be transferred or permanently revoked to fix supply.
- Metadata URLs now load a standard JSON object containing name, symbol,
  description, and image; the signed on-chain snapshot includes a SHA-256 hash.
- Token definitions, associated token-account existence, balances, authority state, supply, and history are rebuilt from confirmed blocks.
- Added token query APIs and a complete browser-wallet token interface.
- Raised the peer protocol to version 5 so older nodes cannot silently disagree about token exchange consensus rules.
- Preserved pre-metadata token serialization and activated required metadata
  snapshots at block 41, keeping existing token blocks and signatures valid.
- Kept legacy HLX transaction serialization unchanged, preserving existing block hashes and chain data.
- Database loading now fails closed and leaves the chain file untouched instead of silently replacing an unreadable chain with genesis.

## Cloudflare wallet

- Allowed read-only token APIs and signed token submissions through the Pages Worker gateway.
- Added confirmed-token discovery, creation, minting, transfers, DAD management, balances, and token transaction details.
- Added a Discover tab with full token and pool details, buy/sell quotes, and
  signed trades; DAD-controlled pool creation remains in Management.
- Added HLX to asset discovery and a DAD-only action for permanently adding
  more HLX liquidity to an active token pool.
- Removed the manual initial token-liquidity field: pool creation accepts only
  an HLX amount and consensus automatically deposits the DAD wallet's entire
  confirmed token balance as the paired reserve.
- Added a bounded recent-chain transaction feed to Nodes; clicking or pressing
  Enter on a row opens full transaction details.
- `HELIX_NODE_URL` now accepts one URL or an ordered JSON array with safe read/transaction failover across up to 10 synchronized nodes.

---

# Helix 0.7.0 — Step 7

## Performance

- Added in-memory indexes for balances, confirmed transactions, total supply, and address history.
- Replaced full-chain transaction lookup with indexed lookup.
- Added bounded pagination to `/history/{address}`.
- Added `/health` for lightweight monitoring.

## Operations

- Added `helixctl status`, `validate`, `backup`, and `compact`.
- Added Python package metadata and console entry points.
- Added installation, operation, security, and maintenance documentation.
- Added a project `.gitignore` that excludes private/runtime state.

## Safety note

Historical blockchain pruning was not enabled because removing old blocks without authenticated state snapshots would weaken or break validation. The maintenance utility only compacts JSON representation and backs up data.
