# Helixchain Conversation Checkpoint

Saved: July 23, 2026

This file summarizes the project decisions and work discussed in the Codex conversation through the current checkpoint. It is a project handoff, not a verbatim transcript.

## Project direction

- Helix is an educational proof-of-work blockchain with wallets, peer nodes, an external Python miner, custom tokens, liquidity pools, token swaps, and a Cloudflare Pages wallet UI.
- The Cloudflare-compatible web application is contained in `web/`.
- Downloads for node and miner packages are made available from the documentation section of the web UI.
- Wallet sessions persist across page refreshes and expire after one hour.
- Login uses a typed username instead of a wallet dropdown, and wallets can be deleted.

## Chain and consensus

- Current peer protocol: version 10.
- Native token: HLX.
- Maximum HLX supply: 20,000,000.
- Mining reward history recorded in the project documentation:
  - Blocks 0-89: 10 HLX.
  - Blocks 90-299: 2 HLX.
  - Block 300 onward: 10 HLX.
- The target block time is 160 seconds.
- Difficulty was reset to 3 at block 161 for one adjustment window. Automatic adjustment resumed at block 171.
- Atomic token swaps activate at block 200. All participating nodes must run protocol 10 before accepting or mining that height.
- Consensus selects the valid chain with the greatest cumulative proof-of-work, not merely the greatest number of blocks.
- Consensus-critical configuration must match across nodes. Different rules can cause an incompatible node to reject valid blocks, have its blocks rejected, and fork from the main network.
- The recommended current `max_difficulty` is 8. Helix difficulty is not directly comparable to Bitcoin difficulty; copying Bitcoin's value or using 64 would be inappropriate. If the ceiling is reached in the future, it should be raised through a coordinated protocol upgrade with an activation height.
- Removing `max_difficulty` is not a supported way to create an infinite ceiling; it may use a program default or cause startup/configuration problems.

## Tokens and markets

- Users can create custom tokens with a DAD authority that manages the token, similar in purpose to a Solana mint authority.
- Token metadata supports JSON containing `name`, `symbol`, `description`, and an image URL.
- Owned tokens appear on the dashboard, while discovery lists tokens created by other users without requiring ownership.
- HLX appears alongside other tokens and has its own statistics, image, supply-issued bar, and history.
- Token detail views include metadata, image, supply distribution, liquidity information, and confirmed price history.
- Users can buy and sell tokens with HLX, add HLX liquidity, and swap between tokens based on their respective HLX values.
- Token price charts use OHLC candlesticks, begin at the left edge, distinguish bullish and bearish candles, provide minute/hour/day/month ranges, allow width and height adjustment, and support wheel zoom and panning.

## Wallet and web UI

- The web mining option was removed in favor of the external Helix Miner.
- The send tab allows selection of the cryptocurrency being sent.
- Transactions and blocks can be clicked for detailed information.
- The network activity view shows blockchain-wide activity in newest-first paginated order.
- Mobile navigation starts on the dashboard and uses a three-bar button that opens a usable right-side drawer.
- Inputs and select menus were restyled to match the interface.
- Pending transactions can be cancelled using a sender-signed cancellation proof that is relayed to peers.
- The site and node were reviewed and hardened against common IDOR, XSS, request-forwarding, and administrative-route issues, while remaining an educational project rather than production financial infrastructure.

## Helix Miner

- The miner's main entry point is Python and can use supporting Python files.
- CPU mining remains supported.
- NVIDIA GPU mining is supported when the appropriate NVIDIA/CUDA dependencies are available.
- The application can select its mining mode and exposes applicable process controls.
- Miner output is scrollable and reports how long each block took to mine.
- The miner polls the chain tip frequently so it abandons stale work when another miner finds a block.

## Peer networking

- Nodes communicate over HTTP API requests rather than a permanent socket connection.
- Peer URLs are stored persistently and bootstrap nodes are read from `config.json`.
- Nodes exchange peer lists, probe `/nodes/info`, and require matching network and protocol values before synchronization.
- Nodes compare cumulative work and pull a heavier valid chain from the best compatible peer.
- Pending transaction IDs are exchanged through mempool inventory messages. Missing transactions are requested, validated, and relayed.
- Newly accepted transactions, cancellations, and blocks are gossiped to known peers while excluding the immediate origin to reduce relay loops.
- Admin API keys are local administrative credentials. Different nodes may use different keys and still exchange blockchain data.
- Non-consensus settings such as ports, public URLs, bootstrap peers, logging, local database paths, and admin keys may differ without creating a fork.
- A future hardening improvement is to expose and compare a deterministic consensus-rules identifier in `/nodes/info` so incompatible configuration is rejected before synchronization.

## Cloudflare Pages and tunnels

- `HELIX_NODE_URL` accepts a JSON array of node URLs, for example:

  ```json
  ["https://node-one.example", "https://node-two.example"]
  ```

- Cloudflare Pages uses its Worker/Functions proxy to contact the selected node, avoiding direct browser mixed-content requests.
- Protected web administration can use `HELIX_ADMIN_API_KEY` and `HELIX_ENABLE_ADMIN_API=true`. The admin key must match the target node for protected operations.
- A TryCloudflare Quick Tunnel can expose a local node without a domain, but its random URL changes whenever the tunnel restarts and it is intended for testing rather than dependable production use.
- `cloudflared` can also run on a Google Cloud VM and proxy its local node at `127.0.0.1:8000`. Without a domain, this still produces a temporary `trycloudflare.com` address.

## Google Cloud node plan

- Recommended starting VM: Google Compute Engine `e2-small`, 2 shared vCPUs, 2 GB memory, and a 20 GB balanced persistent disk. Four GB of memory offers additional headroom.
- The node does not require a GPU. Cloud CPU mining is likely to cost more than its rewards.
- Use Ubuntu 24.04 LTS and reserve a static external IPv4 address.
- Run the Python node as a `systemd` service bound to `127.0.0.1:8000`.
- Use Nginx on public TCP port 80 to proxy requests to the local node. Do not publicly expose port 8000 when using this layout.
- A Google Cloud VM needs a Google firewall ingress rule but does not require home-router port forwarding.
- The Google node should use an established protocol-10 node as a bootstrap peer, synchronize fully, and match chain height and cumulative work before miners use it.
- The Google node's persistent admin key should be stored in a root-readable environment file and reused across restarts.
- The static Google IP is currently more dependable than a Quick Tunnel because it remains stable across process and VM restarts.

## Operational cautions

- Stop or carefully coordinate node processes before copying live chain database files.
- Back up chain data and wallet material before upgrades.
- Do not mine on a newly installed node until synchronization and consensus compatibility have been verified.
- Consensus changes require every participating node to upgrade before the chosen activation block.
- Cloud VM, disk, public IPv4, and outbound network usage can incur charges; configure Google Cloud budget alerts.

## Session addendum — July 24, 2026

### "Website won't connect" — root cause and fix

- The real cause was a Cloudflare Pages **deployment target** problem, not the node. The local git branch is `master`, but the Pages project's production branch differs (Cloudflare default is `main`). `wrangler pages deploy web --project-name=helixwallet` tags the deploy with the current branch (`master`), so it publishes to a **preview** deployment (`master.helixwallet.pages.dev`) and never updates production (`helixwallet.pages.dev`).
- Because Pages **snapshots environment variables at deploy time**, the live production deployment kept an **old TryCloudflare URL** baked into its Worker. After a computer restart, `cloudflared` handed out a new quick-tunnel URL (`sign-pieces-seal-geometry.trycloudflare.com`); the dashboard `HELIX_NODE_URL` was updated correctly, but only preview deploys ever received it. Production's Worker kept fetching the dead old tunnel → **Cloudflare Error 1016 (origin DNS error)**, passed through to the browser.
- It "worked before" because the very first deploy became production automatically; every later `master`-branch deploy went to preview, so production silently froze until the tunnel rotated.
- Fix: deploy to the production branch, e.g. `wrangler pages deploy web --project-name=helixwallet --branch=main` (use whatever Pages → Settings → Builds & deployments → Production branch shows). Permanent option: set the project's production branch to `master` so a plain deploy always hits production.
- Recurring gotchas: TryCloudflare quick-tunnel URLs change every restart and require updating `HELIX_NODE_URL` **and a production redeploy**. A Cloudflare **named tunnel** on an owned domain gives a stable, Worker-resolvable hostname and removes this whole cycle.

### Node security hardening

- `node/security.py` now **never bans loopback** (`127.0.0.1`/`::1`). On a same-host `cloudflared` setup all traffic arrives from loopback; banning it took the whole node offline. Rate-limiting still applies, but the tunnel can no longer self-ban.
- Context: with `trust_loopback_proxy_headers: true`, the node only trusts the Worker's forwarded visitor IP when the Worker's `x-helix-api-key` matches the node's `HELIX_ADMIN_API_KEY`. Generating a **new key every launch** (as the setup commands did) guarantees a mismatch unless Pages is updated too, which collapsed every visitor onto `127.0.0.1` and self-banned the tunnel. Use one **stable** admin key, identical on the node and in Pages.
- Verified end-to-end against the real `node.node` app: match / mismatch / missing-key scenarios, before and after the loopback-ban patch.

### Repository cleanup and web folder consolidation

- Removed dead/regenerable files: `node/database.py` (unused legacy store), `node_8005.json`, all `__pycache__/`, and `.wrangler/tmp/`. Left the two chain-data backups (`database_8000.json.corrupt-*`, `database_8000.json.genesis-reset-*`) in place.
- `web_old/` was deleted (it was the *older* build). `node/node.py` and the `tests/*.mjs` suite were repointed from `web_old/` to `web/`. **`web/` is the canonical build** that gets deployed and that the local node serves.

### Token price chart changes

- Re-added candle **interval options — Minute / Hour / Day / Month / Auto** — via `TOKEN_CHART_RANGES` and a forced `TOKEN_CHART_INTERVAL` honored by `chartCandleInterval`.
- Added a **Start slider** (`#token-chart-start`) that chooses when the chart begins. Because the Y-axis autoscales to the visible window, cropping the start excludes early/large spikes so small values stay readable — this is the intended fix for "big data points overpowering small ones."
- `token-metadata.example.json` is a free-form example; the token test now uses an inline fixed sample for browser/node hash-parity instead of depending on the shipped file's contents.

### Test status

- 27 Python tests pass (`tests/`, excluding `test_helix_miner.py`, which needs `tkinter` and cannot run headless) and all 10 `.mjs` web tests pass, including new coverage for the chart interval/start controls.

## Session addendum 2 — July 24, 2026 (features)

### Dashboard, token lists, chart

- **Token lists show one per line.** `.token-list` CSS changed from a multi-column auto-fit grid to `grid-template-columns:1fr`, so the Dashboard, My Tokens, and Discover lists are vertical.
- **Total wallet value at the top of the Dashboard.** The big number is now the whole wallet's worth priced in HLX (HLX balance plus each held token converted through its pool price: `value_HLX = balance_units * pool_hlx_reserve / pool_token_reserve`, decimals cancel), via `walletTotalValueHlx()`. HLX is the stable unit of account; the HLX row in the token list still shows the raw HLX held. Labeled as total value.
- **Chart Start is now a date/time input.** The earlier Start *slider* was replaced with an `<input type="datetime-local">` (`#token-chart-start`) bounded to the data range; `toLocalDatetimeValue()` formats it, and picking a start re-renders so the Y-axis rescales. Interval buttons (Minute/Hour/Day/Month/Auto) remain.

### DAD token burn

- New `token_burn` transaction type (added to `Transaction.TOKEN_TYPES`; not zero-amount). Only the token's **DAD authority** can burn; it destroys tokens from the DAD's own balance (`receiver == sender`) and lowers total minted supply. Enforced in `blockchain._apply_token_transaction` (DAD check, sufficient balance, receiver==sender) and indexed in `_rebuild_indexes`.
- Frontend: red **Burn** button in Management (shown for DAD with a non-zero balance) + `submitTokenBurn()`.
- **Consensus note:** this is a new tx type, so every node must run the updated build before burns relay/confirm network-wide. Not yet gated behind a protocol bump/activation height — offered but not done.

### Dedicated Swap tab

- Added a **Swap** tab/pane in the Tokens section (`token-pane-swap`) with source + target selects, amount, live routed quote, and submit — `renderSwapPane()`, `updateStandaloneSwapQuote()`, `submitStandaloneSwap()`. Reuses the existing `token_swap` payload, HLX routing, 0.3% fees, and 1% slippage guard. The in-market swap still exists too.

### Mining pool (new)

- **`pool_server.py`** — a hostable pool coordinator (FastAPI). Fetches block templates addressed to the pool wallet, serves jobs at a reduced **share difficulty**, validates/counts shares, submits winning blocks, and pays miners **proportionally to shares** (`(reward - fee) * shares_i / total`, floored; fee + remainder kept). Endpoints: `/pool/info`, `/pool/work`, `/pool/submit`, `/pool/stats`. Config via env: `HELIX_POOL_SEED` (payout wallet), `HELIX_POOL_NODE`, `HELIX_POOL_FEE_PERCENT` (default 1), `HELIX_POOL_SHARE_SUBTRACT` (default 2), `HELIX_POOL_PORT` (default 8100).
- **`run_pool.py`** — launcher (uvicorn, warns if no seed/address).
- **`helix_miner.py`** — added a **Mining mode** selector (Solo/Pool) + **Pool URL** field. Pool mode fetches `/pool/work`, mines shares continuously at the share target (CPU via new `_share_worker`, and CUDA), and submits each share to `/pool/submit`; refreshes when the pool advances. Solo path unchanged.
- Docs tab has a **Mining pools** section (host + join). Miners never share keys; only the host holds the pool wallet.

### Tests

- 37 Python tests pass (added `tests/test_token_burn.py` and `tests/test_pool_server.py`; still excludes `test_helix_miner.py` which needs `tkinter`). All 10 `.mjs` web tests pass, with added coverage for burn, swap tab, wallet-value, datetime start, and one-per-line lists.

### Deferred (next session)

- **Fine-grained, Bitcoin-style difficulty** (numeric target instead of 16×-per-hex-zero). NOT started, at the user's request. Plan: represent difficulty as a target `int(hash,16) <= target`; work = `MAX_TARGET/target`; smooth bounded retarget on actual/expected time ratio; **activation height** so blocks below it keep the leading-zero rule (avoids forking the height-750 chain); update `/mining/work` to return the target, the miner's solution check, and the `miner_cuda.py` kernel. Consider a protocol bump.
- Reminder: deploy the web UI to the **production branch** (`wrangler pages deploy web --project-name=helixwallet --branch=main`); burn and pool require all nodes on the updated build.

## Session addendum 3 — July 24, 2026 (fine-grained difficulty)

### What changed

- Proof of work is now a **Bitcoin-style numeric target**: a block is valid when `int(hash, 16) <= target`. Leading-zero difficulty `D` is exactly the special case `target = 16**(64 - D) - 1`, so the legacy rule is a subset and existing blocks stay valid.
- **Smooth retarget** (`Blockchain.expected_target`): the target moves by the ratio of actual-to-expected block time, bounded to a 4x change per window and clamped to the configured `min_difficulty`/`max_difficulty` range — so difficulty can settle *between* whole hex levels instead of jumping 16x. Verified by a test that lands strictly between difficulty 4 and 5.
- **Activation-gated** by `fine_difficulty_activation_height` (default **100000000**, i.e. dormant). Below it: legacy leading-zero rule, unchanged. At/above it: numeric target. Set it **above the current chain tip** and upgrade **every node + the pool** before that height or nodes fork.

### Key implementation points

- `node/blockchain.py`: added `MAX_HASH`, `Block.mine_to_target(target)`, `difficulty_to_target()`, `hash_meets_target()`, `expected_target()`. `_validate_block_against_state` now checks `hash_meets_target(block.hash, expected_target(...))`. `block_work` = `16**difficulty` below activation, `MAX_HASH // (target + 1)` above. `create_mining_candidate` returns `(block, difficulty, target)`; `mine_pending_transactions` uses `mine_to_target`. `Block.mine(difficulty)` and `expected_difficulty()` kept for compatibility/display.
- `node/node.py`: `/mining/work` returns exact `target` (64-hex) alongside `difficulty`/`target_prefix`; `/stats` adds `next_target` and `fine_difficulty_active`. Config default added.
- `config.json`: `blockchain.fine_difficulty_activation_height` (dormant default).
- `helix_miner.py`: `work_target()` helper; CPU workers (`_hash_worker`, `_share_worker`) and solo/pool round managers check `int(hash,16) <= target`, using the node/pool `target`/`share_target`.
- `pool_server.py`: reads node `target`; `share_target = min(MAX_HASH, network_target * 16**share_subtract)`; `submit_share` and hashrate use numeric targets (with difficulty fallbacks so older payloads/tests still work); `/pool/work` returns `share_target`/`network_target` hex.
- `miner_cuda.py`: `prepare(block, target)` derives a leading-zero pre-filter from the target and `mine_batch` verifies the exact target on the CPU side (returns no-solution instead of raising when only the pre-filter passed).

### Tests

- Added `tests/test_fine_difficulty.py` (5 tests): legacy equivalence, dormant-default equals legacy, `mine_to_target` validity, fine-grained retarget landing between levels, and bounds/direction. Full suite now **42 Python** (excl. `test_helix_miner.py`, needs tkinter) + **10 web** tests passing. End-to-end mine with activation at height 1 produces valid blocks and a fully-validating chain.

### To enable

- Set `blockchain.fine_difficulty_activation_height` in `config.json` to `current_tip + ~20`, deploy the build to all nodes and the pool, restart before that height. Consider bumping the protocol number so pre-upgrade nodes can't join.

### Auto-adjust refinement (same session)

- The fine-difficulty retarget now uses **`fine_target_block_time_seconds` (default 120 = 2 minutes)** and runs every `difficulty_adjustment_interval` (10) blocks: if the window's average block time is **below 2 min it raises** difficulty (smaller target), **above 2 min it lowers** it (larger target). Standard, stable direction.
- **No upper difficulty cap** anymore: `expected_target` floors the target at `min_difficulty` (largest target) but has no `max_difficulty` ceiling, so difficulty rises without limit as hashrate grows — no manual `max_difficulty` bumping. Still bounded to a 4x move per window. `max_difficulty` remains only for the legacy pre-activation path/display.
- Config keys added: `blockchain.fine_target_block_time_seconds` (120). Tests updated: `tests/test_fine_difficulty.py` now covers the 2-minute direction, uncapped upward rise past the old ceiling, and the min_difficulty floor. Suite: **44 Python + 10 web** passing.
