# Helix networking refactor — Step 1

## Changed

- Added `config.json` for node and networking settings.
- Added `node/peer_manager.py` for thread-safe peer persistence in `peers.json`.
- Refactored `node/node_manager.py` so node identity and peer storage are separate.
- Updated `node/node.py` to load discovery ports, sync interval, and node port from configuration while preserving environment-variable overrides.
- Updated `wallet/network.py` to use configured nodes, automatic failover, and a small healthy-node cache.
- Existing `node_<port>.json` files are migrated automatically: any embedded `peers` entries are copied into `peers.json` and removed from the node identity file.

## Environment overrides retained

- `NODE_PORT`
- `HELIX_CONFIG`
- `HELIX_DISCOVER_PORTS`
- `HELIX_SYNC_INTERVAL`
- `HELIX_PEERS_FILE`
- `HELIX_NODE_FILE`
- `HELIX_WALLET_NODES`

## Tests performed

- Python compilation of every included `.py` file.
- Peer add/remove, normalization, duplicate prevention, and JSON persistence.
- Node identity creation without embedded peer storage.
- Wallet default-node configuration.
- Full import of `node.node` with temporary database, peer, and identity files.

## Step 2: Internet peer network

- Added persistent peer metadata and health scoring in `node/peer_manager.py`.
- Added compatibility-aware peer probes in `node/peer_health.py`.
- Added internet bootstrap discovery in `node/bootstrap.py`.
- Added `/nodes/info` and `/nodes/peers` endpoints.
- Chain synchronization now selects one compatible, highest-chain peer instead of downloading full chains from every peer.
- Nodes exchange version, protocol, network, height, latency, and capability information.
- Repeatedly failing non-bootstrap peers are automatically removed.

## Step 3: Transaction propagation and mempool relay

- Added `node/mempool.py` for relay-loop prevention, TTL tracking, and controlled rebroadcasting.
- Added transaction inventory endpoints so peers exchange IDs before downloading full transactions.
- Added `/p2p/transaction`, `/p2p/inventory`, `/mempool/inventory`, `/mempool/transaction/{tx_id}`, and `/mempool/stats`.
- Pending transactions now persist a `received_at` timestamp and expire according to `config.json`.
- Added a configurable pending-transaction limit.
- Newly accepted blocks are relayed to other peers, while duplicate blocks stop naturally at validation.
- Node version is now `0.3.0` with `mempool-gossip` and `block-relay` capabilities.


## Step 4: Consensus resilience

- Chain selection now uses accumulated proof-of-work instead of length alone.
- Added deterministic difficulty adjustment with configurable activation height, interval, target block time, and bounds.
- Added an in-memory bounded orphan-block pool with TTL pruning and automatic attachment when parents arrive.
- Added configurable hard checkpoints. Empty checkpoints remain the safe default until trusted hashes are published.
- Chain reorganizations preserve valid transactions from detached blocks by returning them to the mempool.
- Added `/consensus/status` and `/consensus/orphans` endpoints.
- Peer info advertises chain work and the next expected difficulty.
- Node version is now `0.4.0`; the consensus protocol is now `2` so pre-Step-4 nodes cannot accidentally join the upgraded network.


## Step 5 - Wallet and key management

- Added versioned encrypted wallet records using scrypt for new and upgraded wallets.
- Preserved legacy account-0 key derivation and automatic PBKDF2 wallet migration on unlock.
- Added atomic wallet-store writes, password changes, encrypted backups, deletion, and watch-only wallets.
- Added deterministic secondary account derivation while preserving all existing addresses.
- Expanded wallet history to include confirmations, pending transactions, confirmed balance, and available balance.
- Replaced the stale `backups.transaction` CLI import with `node.transaction`.
- Added CLI commands for history, status, wallet metadata, locking, password changes, backups, and watch-only addresses.

## Step 6 - Security and network hardening

- Added `node/security.py` with per-IP rate limiting, violation tracking, persistent temporary bans, request-body limits, and optional admin API-key protection.
- Restricted CORS to configured local origins instead of allowing every origin.
- Added strict validation for addresses, transaction IDs, signatures, public keys, blocks, inventory lists, node registrations, and chain-sync payloads.
- Prevented unregistered transaction inventory origins from triggering outbound requests and normalized peer callback URLs to reduce SSRF risk.
- Added `/security/status` for operational visibility.
- Added `run_node.py`, which disables proxy-header trust and can enable HTTPS using configured certificate and key files.
- TLS and admin API-key enforcement are opt-in so existing local development remains compatible. For an internet-facing node, enable both and set `HELIX_ADMIN_API_KEY` in the environment.
