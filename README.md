# Helix Coin 1.1.0

Helix is an educational proof-of-work cryptocurrency project with encrypted wallets, custom tokens, NFTs, peer discovery, mempool gossip, block relay, fork handling, checkpoints, dynamic difficulty, and network hardening.  

## Updates

### 2026-08-02 (modern miner and CLI)

- **Wallet-matched miner UI.** The desktop miner now uses the wallet's dark
  Helix palette, logo, cards, status colors, responsive single-column layout,
  cleaner inputs, highlighted live metrics, and color-coded scrollable logs.
- **Headless CLI miner.** `helix_miner_cli.py` supports solo and pool mining,
  CPU process selection, NVIDIA mode, multiple node URLs, rate updates, and
  clean Ctrl+C shutdown without requiring tkinter.

### 2026-07-29 (desktop downloads)

- **Windows applications.** The wallet, CPU miner, and node setup GUI now ship
  as Windows executables. The miner and node ZIPs include their EXEs, while the
  wallet has a dedicated Windows ZIP.
- **Linux wallet launcher.** The wallet download includes an executable shell
  launcher, Helix icon, standard `.desktop` file, and per-user installer.
- **Cloudflare-compatible packaging.** Desktop downloads are split so every
  static file remains below Cloudflare Pages' 25 MiB per-file limit. Mobile
  devices continue to use the installable PWA.

### 2026-07-28 (wallet analytics and chart controls)

- **Wallet-worth leaderboard.** The wallet now ranks funded public addresses by
  confirmed HLX plus custom-token holdings valued at their current confirmed
  HLX-pool spot price. Entries are paginated and open a candlestick history of
  that address's estimated worth.
- **Transparent valuation limits.** NFTs and tokens without active HLX
  liquidity are excluded, and the UI warns that pool spot prices can be
  manipulated and do not guarantee the amount obtainable by selling.
- **NFT chart controls fixed.** Minute, Hour, Day, Month, Auto, Fit all,
  start-time, width, and height controls now work inside the NFT detail modal,
  with the same pan and wheel-zoom behavior as token charts.

### 2026-07-27 (protocol 15 foundation)

- **Replay-protected transactions.** Upgraded wallets sign `chain_id`, an account
  `sequence`, and `valid_until_height`, preventing cross-chain replay and
  expiring abandoned submissions.
- **On-chain cancellation and replacement.** A pending transaction can be
  replaced only by the same sender and sequence with a higher fee. The wallet's
  Cancel button submits a signed zero-value cancellation replacement.
- **Transactional storage and explorer index.** Nodes migrate a validated JSON
  chain into SQLite/WAL, retain the JSON recovery export, create periodic
  snapshots, and atomically index blocks and transactions.
- **Block commitments.** From block **1000**, every block commits to a transaction
  Merkle root and the resulting HLX/token/NFT state root. Published protocol
  vectors lock canonical encodings and commitment calculations.
- **Operations and releases.** `/health/details` provides actionable warnings,
  `/metrics` exposes Prometheus data, and `tools/release_manifest.py` creates and
  verifies Ed25519-signed release manifests.
- **Pool protocol.** Pools use a rolling PPLNS work window and per-miner vardiff;
  miners refresh automatically when their assigned share target changes.
- **Deployment.** Protocol 15 rejects older peers. Upgrade node, miner, pool, and
  web files together. Envelope and commitment enforcement is reserved for block
  **1000**; no chain reset is required.

### 2026-07-27 (security audit, protocol 14)

- **External-only proof-of-work.** Nodes no longer expose `/mine`, `/mine/start`,
  or mining-job status routes, so an admin key cannot make a node spend CPU on
  proof-of-work. Helix Miner and pools still fetch templates and submit proofs
  through `/mining/work` and `/mining/submit`.
- **Downloadable pool GUI.** `helix-pool.zip` now provides a Python setup and monitoring app for pool wallet/node settings, dependency installation, process control, live shares/miners/hashrate, logs, and named or temporary Cloudflare tunnels.
- **Cloudflare token inputs.** Both pool and node setup GUIs accept masked named-tunnel tokens and run `cloudflared tunnel run --token …` without saving the token to their settings or printing it in logs.
- **Signature-replay defense.** Wallet signatures are normalized to canonical low-S ECDSA. Nodes reject malleated high-S submissions immediately, track a signature-equivalent canonical ID, and enforce canonical signatures in consensus from block 200. This prevents an attacker from changing a visible signature into a second valid transaction ID and replaying an asset transfer.
- **Self-hosted signing code.** The web wallet no longer downloads secp256k1 code from a third-party CDN. The pinned Noble Curves 2.2.0 signing bundle is included in `web/secp256k1.js`, and the Content Security Policy now permits scripts from the wallet origin only.
- **Gateway hardening.** Cloudflare node targets must use HTTPS except for loopback-only local development. The gateway strips cookies, authorization credentials, Cloudflare Access assertions, and referrers before forwarding requests to a node.
- **Browser and admin defenses.** HSTS and cross-origin isolation headers protect the Pages deployment; the node-served wallet now receives CSP, anti-framing, MIME-sniffing, referrer, and permissions headers too. Node registration and security status routes are included in the fail-closed admin route set.
- **Protocol 14.** This security release is superseded by protocol 15. The full report is in `SECURITY_AUDIT_2026-07-27.md`.

### 2026-07-27 (NFT management, protocol 13)

- **Manage NFTs.** Owners can create, edit, or cancel a fixed-price NFT listing from one management view. Editing the asking price preserves every active escrow-backed bid.
- **View and accept every bid.** The management view shows all active bids from highest to lowest, including each bidder and amount, and lets the owner accept any selected bid.
- **Creator-controlled royalties.** Only the NFT creator can update its royalty, and only while the creator still owns it before its first transfer or sale. The first ownership change permanently locks the royalty, even if the NFT later returns to the creator.
- **Protocol 13.** Royalty updates and their permanent lock are consensus rules. Upgrade and restart every node before using this release; no chain reset is required.

### 2026-07-27 (transaction fees, protocol 12)

- **Signed network fee.** Every newly submitted transaction includes a configurable minimum fee (currently **1 HLX**) inside its signed payload. Changing the amount or fee invalidates the signature. The sender must have enough confirmed HLX for both the operation and its fee.
- **Fees go to miners.** The miner confirming a block receives all fees in that block in addition to the 10 HLX subsidy. Fees move existing HLX and therefore do not increase issued supply or bypass the 20,000,000 HLX cap.
- **Safe activation.** Existing fee-less signatures remain valid below block 200; from block 200 onward every transaction must include at least the configured fee. Upgrade and restart every node on protocol 12 before activation. No chain reset is required.
- **Transaction parser compatibility.** Fee-less transactions created by a cached pre-fee wallet are parsed normally during the grace window instead of being mislabeled as malformed. A parser contract test now round-trips every supported transfer, token, liquidity, swap, and NFT transaction type through the public node format.

### 2026-07-26 (NFT marketplace, protocol 11)

- **On-chain NFT discovery and markets.** The wallet now has My NFTs, Discover, and Create NFT tabs. Owners can list NFTs for HLX, buyers can purchase a listing atomically, and users can place, raise, or cancel escrow-backed bids. Owners can accept a bid, transferring the NFT and paying the seller plus the NFT's creator royalty in the same confirmed transaction. Losing and cancelled bids are refunded by consensus. Displayed market value prefers the last confirmed sale, then the highest escrow-backed bid, and labels an unsold listing as an asking price rather than a proven value.
- **Signed ownership actions.** Mint, transfer, list, cancel, bid, accept, and buy transactions are signed by the initiating wallet's secp256k1 private key. The key remains in the browser; nodes independently verify the signature, derived sender address, current ownership, balances, and exact signed fields.
- **Protocol 11.** NFT marketplace operations are consensus rules. Upgrade and restart every node before confirming marketplace transactions; protocol-10 nodes are intentionally incompatible.

### 2026-07-26 (block-1 relaunch)

- **Fresh genesis with every rule active from block 1.** The chain was reset and all historical phase-in heights collapsed to 1: a flat **10 HLX** reward per block (no 10→2→10 schedule), fine-grained difficulty seeded at **5.5** toward 10-minute blocks, **retargeting every 100 blocks** (`difficulty_adjustment_interval` = 100, first retarget at block 101, no reset height), and tokens, liquidity pools, atomic swaps, NFTs, and the native HLX DAD identity all active from block 1. This is a consensus break — every node must reset chain data and run this build. Previous chain data is preserved under `chain_backup_*/`.

### 2026-07-26

- **NFTs.** Consensus-backed one-of-a-kind tokens have a unique id, creator, single owner, on-chain metadata, signed SHA-256 content hash, and creator royalty. The wallet now separates **My NFTs**, **Discover**, and **Create NFT**, while the marketplace supports signed listings, escrow-backed bids, bid cancellation, direct purchases, and owner acceptance. Confirmed sales, active asks, and bids provide clearly labelled market-value signals. Only the current owner can transfer or list an NFT, and every marketplace action is signed by the acting wallet. Update every node — it is a consensus feature.
- **Block-timestamp fix.** Fast, low-difficulty blocks that share a clock tick (or miners that stamp whole seconds) were wrongly rejected as "another miner won this height." A child block may now sit up to a small tolerance behind its parent (still capped to the near future), and `/mining/submit` now returns the **actual** rejection reason instead of a vague catch-all. Consensus rule — update all nodes.
- **Wallet quality-of-life.** Payment-request **QR codes and shareable links** (address + amount), an in-app **camera QR scanner** on Send, a saved-contacts **address book**, a **confirmation-depth** counter on mined transactions, opt-in **desktop notifications** when a pending transaction confirms, **installable PWA** (desktop and mobile, offline-capable), and an **Explorer** tab for browsing blocks, transactions, and addresses with a network-difficulty chart.
- **Auto-checkpoints.** The node periodically records a checkpoint at a safely buried height to harden deep history against long-range reorgs, with no manual configuration.
- **Difficulty retarget interval change.** The fine-difficulty retarget now runs every 10 blocks through block 50 and every **100 blocks from block 50 onward** (`difficulty_interval_change_height` = 50, `difficulty_new_adjustment_interval` = 100); the window ending at block 50 is a one-time shorter transition. Boundaries below the change height keep the original 10-block cadence so earlier blocks stay valid. Consensus rule — set the change height above the current chain tip and upgrade all nodes together.
- **HLX minting chart.** The Helix (HLX) detail view now shows a candlestick chart of coin issuance over time — reusing the token-chart engine (interval picker, pan, zoom, resize) but plotting cumulative minted supply instead of a pool price, so each candle's height is the HLX minted in that interval. Backed by a new read-only `GET /network/mint_history`.

### 2026-07-24

- **Bitcoin-style fine-grained difficulty.** Proof of work can use a numeric target (a block is valid when `int(hash, 16) <= target`) that retargets smoothly every 10 blocks toward a target average block time — no upper cap (floored at `min_difficulty`), bounded to a 4x move per window. It is gated by `blockchain.fine_difficulty_activation_height` so existing chains stay valid; below that height the classic leading-zero rule is byte-for-byte unchanged. The retarget aims for a **10-minute** average block time (`fine_target_block_time_seconds`) and seeds from a configurable starting difficulty that may be fractional (`fine_initial_difficulty`, e.g. **5.5**).
- **Mining pools.** New `pool_server.py` / `run_pool.py` let anyone host a pool that pays miners proportionally to the shares (hashrate) they contribute, minus a configurable fee. Helix Miner gained a **Pool** mode, and the wallet has a shared **Pools** directory tab that lists pools (fee, active miners, online status) and gossips them across nodes.
- **DAD token burn.** A new `token_burn` transaction lets the DAD authority destroy tokens from its balance and lower the total minted supply.
- **Dedicated Swap tab**, a **total wallet value** (priced in HLX) at the top of the Dashboard, and token lists that show one asset per line.
- **Encrypted wallet backup/restore** to and from a file, from the Dashboard and the Recover screen.
- **Peer and pool gossip** so a peer or pool added on one node propagates network-wide; the Nodes tab shows real connected/disconnected status from live probes.
- **Optional admin API key.** Running a node no longer requires a key or hosting a website; set `HELIX_REQUIRE_ADMIN_API_KEY=true` (plus `HELIX_ADMIN_API_KEY`) only to lock down a public node.
- **One-click setup.** `setup.bat` opens a small GUI installer (`install_node.py`); `start-node.bat` / `start-node.sh` do the same from the command line and skip installing libraries that are already present.
- Chart candle interval options (Minute / Hour / Day / Month / Auto) and a date-and-time chart-start picker.

### 2026-07-23

- Added a dedicated, numbered Activity view for all confirmed blockchain transactions across every wallet, newest first, with full clickable details.
- Added native HLX to Dashboard, My Tokens, and Discover with network supply, reward, difficulty, and chain statistics.
- Added downloadable Helix Miner and full-node packages plus an in-wallet Docs section covering wallet, token, mining, node, tunnel, and maintenance workflows.
- Added versioned adaptive difficulty: a 600-second target from block 60, followed by a one-time reset to difficulty 3 and a 160-second target from block 161.
- Added TradingView-style OHLC candlestick charts with real time spacing, red/green candles, panning, wheel zoom, and manual width/height controls.
- Added atomic token-to-token swaps routed through both tokens' HLX pools with signed slippage protection.
- Added multi-asset Send, mobile layouts, pending-transaction cancellation, persistent one-hour browser sessions, and local wallet deletion.
- Added an optional NVIDIA CUDA backend to Helix Miner with CPU verification of every GPU-discovered proof.
- Restored the 10 HLX mining reward from block 300 onward.
- Reset proof-of-work difficulty to 3 at block 161 under peer protocol 10; automatic 10-block adjustments resume after a complete post-reset window.

## How the blockchain works

**Blocks and the chain.** The chain begins with a fixed, empty genesis block.
Every block after it contains a list of transactions plus exactly one mining
reward, is identified by its SHA-256 hash, and references its parent by that
parent's hash. Altering anything in a block changes its hash and breaks every
block that follows, which is what makes the history tamper-evident.

**Proof of work and difficulty.** A block is valid only if its hash, read as a
number, is at most the current **target**: `int(hash, 16) <= target`. Miners
vary a nonce until the hash falls under the target; a smaller target is harder.
Helix uses a fine-grained numeric target, so difficulty is continuous instead of
jumping in 16x steps: `difficulty = 64 - log16(target + 1)`, and it may be
fractional. The chain seeds at difficulty **5.5** from block 1 and retargets
every 100 blocks toward a **10-minute** average block time. Each adjustment scales
with how far the recent average was from target (a burst of very fast blocks
hardens far more than slightly-fast ones), bounded to a large but finite move per
window (`fine_max_adjust_factor`), with no upper cap and a floor at the minimum
difficulty. See `blockchain.expected_target`.

**Transactions.** Transactions are signed with secp256k1 keys held only in the
user's browser — the network is non-custodial. Besides a plain HLX transfer, a
transaction can create a token, mint, transfer, change a token's DAD authority,
create a liquidity pool, add HLX liquidity, buy, sell, swap, or burn. A submitted
transaction stays **pending** in the mempool until a miner includes it in a block.

**Mining and rewards.** Mining runs on the miner's own hardware, not the node: a
miner pulls a work template (`GET /mining/work`), hashes it locally on CPU, GPU,
or through a pool, and submits the solved block (`POST /mining/submit`). Each
valid block pays its miner a single `SYSTEM` reward transaction — the only way
new HLX is ever created, and never beyond `max_supply`.

**Consensus (which chain is real).** Nodes follow the chain with the most
**accumulated proof-of-work** (`chain_work = sum of MAX_HASH // (target + 1)`),
not merely the longest. If two miners find a block at the same height at once, the
network briefly splits and each node keeps the block it saw first; `replace_chain`
only switches when another branch has strictly more work. The tie breaks when the
next block extends one branch, making it heavier — every node then reorganizes
onto it. The abandoned block is **orphaned**: its ordinary transactions return to
the mempool, and its reward is discarded, so only the winning miner is paid.
Configured **checkpoints** prevent any reorg from rewriting history past a fixed
point.

**Networking.** Nodes communicate over HTTP. A new node joins by contacting a
bootstrap **seed** (shipped: `https://node.hlxchain.com`), then discovers the rest
through peer gossip. Every 30 seconds each node discovers peers, pulls the
heaviest chain available, and re-audits every block's hash.

**Tokens and swaps.** Custom tokens trade against HLX through constant-product
liquidity pools with a 0.3% fee. HLX is the base asset and the stable unit of
account the wallet prices everything in.

## Requirements

- Python 3.11 or newer
- A writable project directory for the JSON blockchain database and wallet store

## Install

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -e .
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -e .
```

## Run a node

Anyone can run a node — no admin key and no website required. A node serves the
browser wallet locally at `http://127.0.0.1:8000/`, so hosting the Cloudflare
Pages site is optional. To join others, add their node as a peer (or a
`bootstrap_node` in `config.json`); peer and pool lists then gossip across the
network automatically.

Download the node software here: [Releases](https://github.com/ProJackson355/Helixchain/releases)

**Easiest (Windows):** extract the zip and double-click **`setup.bat`** to open a
small installer window — fill in the settings (most are optional), and it creates
the environment, installs any missing libraries, and starts the node. Or
double-click **`start-node.bat`**. On Linux/macOS run `bash start-node.sh`
(add `--gui` for the installer).

**Manual:**

```bash
python run_node.py
```

The default API listens on port `8000`. Edit `config.json` or set environment
variables such as `NODE_PORT`, `HELIX_DATABASE`, and `HELIX_CONFIG`. An admin key
is optional; set `HELIX_ADMIN_API_KEY` and `HELIX_REQUIRE_ADMIN_API_KEY=true`
only to protect a public node's admin endpoints.

Health check:

```bash
curl http://127.0.0.1:8000/health
```

If you expose a node with TryCloudflare, verify its public `/health` endpoint,
then submit the working `trycloudflare.com` URL from the wallet's **Nodes** tab
("Submit your node for the shared list") so it can be considered for the Helix
node list. Temporary TryCloudflare URLs change when the tunnel restarts.

### Running a shared network (seed / bootstrap nodes)

New nodes join a network by connecting to a **bootstrap (seed) node** on
startup, then discovering everyone else through peer/pool gossip. This build
ships with the public seed **`https://node.hlxchain.com`** in
`network.bootstrap_nodes`, so a downloaded node auto-joins the Helix network on
startup with no configuration. To point nodes at a different network, change the
seed in either place:

- `network.bootstrap_nodes` in `config.json` (a JSON array), or
- the `HELIX_BOOTSTRAP_NODES` environment variable (comma-separated URLs), which
  merges with the config list and needs no file edit. For a stable
seed that survives restarts, run your node behind a **named Cloudflare Tunnel**
on a domain you own (e.g. `https://seed.yourdomain.com`) rather than a temporary
TryCloudflare URL, and use that as the bootstrap value. Every downloaded node
then auto-joins your network on startup.

### Running a permanent node for free

A "permanent" node needs a **stable public address** and a **machine that stays
on**. You can get both without paying — options below, most robust first.
Whatever address you end up with, put it in the installer's **Public URL** field
(or `network.public_url` in `config.json`) and the node advertises it and
registers with the seed automatically.

- **Oracle Cloud "Always Free" VM** — a free-forever cloud server (generous ARM
  allowance) with a **permanent public IP**. Run the node there so it's always on
  *and* reachable — no home PC required. Point a DNS name at the IP or run
  `cloudflared` on the VM for HTTPS. Closest thing to a real permanent node
  without paying.
- **Tailscale Funnel** — free, stable HTTPS hostname like
  `mynode.tailnet.ts.net`, no domain and no port forwarding, works behind CGNAT.
  Run the agent next to the node and expose port 8000; the home machine just has
  to stay on.
- **ngrok free static domain** — the free plan includes one fixed
  `*.ngrok-free.app` subdomain that doesn't rotate like the quick tunnel.
- **playit.gg / Pinggy** — free tunnels that also work behind CGNAT (some free
  URLs rotate — check before relying on them).
- **Home port-forward + free dynamic DNS (DuckDNS)** — forward port 8000 and
  point a free `you.duckdns.org` name at it. Only works with a real public IP
  (not CGNAT), and exposes your home IP.

The catch on every home option: the computer must stay powered on to be
reachable, so an always-free cloud VM is the only way to get "permanent" without
paying *or* leaving a PC running 24/7. Everyone else can keep using the free
quick tunnel — it just rotates its URL on each restart. The shipped seed
`node.hlxchain.com` handles bootstrap either way.

## Helix Miner

Download the miner here: [Releases](https://github.com/ProJackson355/Helixchain/releases)  
Start a node, then launch the Python desktop mining app:

```bash
python helix_miner.py
```

Enter the wallet address that should receive block rewards and one node URL,
such as `http://127.0.0.1:8000`. Multiple local or TryCloudflare node URLs may
be entered as a comma-separated list or JSON array. Helix Miner uses multiple
Python processes to hash locally, detects within about one second when another
miner wins the height, and submits solved blocks through `/mining/submit`. The
log records how long this miner worked on every completed round.

For NVIDIA mining, install the optional CUDA package and select **NVIDIA CUDA**
in Helix Miner:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-nvidia.txt
.venv\Scripts\python.exe helix_miner.py --backend nvidia
```

`requirements-nvidia.txt` targets CUDA 13. For an NVIDIA driver using CUDA 12,
install `cupy-cuda12x[ctk]` instead. Do not install multiple CuPy packages in
the same environment. GPU proofs are recalculated with the CPU consensus hash
before submission; CPU mode remains available without CuPy.

### NVIDIA GPU compatibility

- Requires an NVIDIA CUDA-capable GPU with compute capability 3.0 or newer and
  a compatible NVIDIA driver/runtime combination.
- Typical families include modern GeForce RTX, NVIDIA RTX/Quadro, Tesla, and
  NVIDIA data-center GPUs. The backend is hardware-tested on an RTX 4050 Laptop
  GPU.
- CUDA 12 and CUDA 13 are supported through their matching CuPy packages on
  Windows and Linux. Run `nvidia-smi` to identify the driver-reported version.
- The current release uses the first detected NVIDIA GPU. Multi-GPU mining is
  not yet implemented.
- AMD, Intel, Apple Silicon, and other non-CUDA GPUs are not supported; use CPU
  mining on those systems.

Older cards are supported only when the installed NVIDIA driver and selected
CUDA runtime still support that exact model. CuPy's current installation
requirements are the authoritative compatibility reference.

The browser wallet no longer mines blocks. Its Send tab still lists pending
transactions and allows their original sender to cancel them before mining.

On the relaunched (block-1) chain, difficulty uses the fine-grained numeric
target from block 1, seeded at 5.5 and retargeting every 100 blocks toward a
10-minute average (the first retarget is at block 101); there is no reset
height. The target is probabilistic, so an individual block can take more or
less than 10 minutes.

## Mining pools

A pool combines several miners' hashrate and shares block rewards, so payouts
arrive more steadily than solo mining. Anyone can host one.

**Host a pool:**

```bash
# set the pool's payout wallet (its 12-word seed) and point it at a node
set HELIX_POOL_SEED=word word word ... word         # Windows (export on Linux/macOS)
set HELIX_POOL_NODE=http://127.0.0.1:8000
python run_pool.py                                   # serves on port 8100
```

Optional: `HELIX_POOL_FEE_PERCENT` (default 1), `HELIX_POOL_SHARE_SUBTRACT`
(initial share difficulty reduction, default 2), `HELIX_POOL_PORT` (default
8100), `HELIX_POOL_PPLNS_WINDOW` (default 10,000 accepted shares), and
`HELIX_POOL_SHARE_SECONDS` (vardiff target, default 15 seconds). Expose port 8100
with its own tunnel and share that URL with miners. Block templates are addressed
to the pool wallet; when a member solves a block the reward is split by each
miner's weighted work in the rolling PPLNS window and paid out
on-chain, with the fee kept by the operator. The pool reserves the network fee
for each signed payout transaction before splitting the round income. Payouts are whole HLX, so a 1% fee
on a 10 HLX reward rounds to 0 — raise the percentage for a reliable cut.
`GET /pool/info` and `GET /pool/stats` expose live pool data.

**Join a pool:** in Helix Miner, set **Mining mode** to **Pool**, paste the pool
URL and your reward address, and start. You mine at a reduced share difficulty
and submit shares continuously. The wallet's **Pools** tab is a shared directory
of pools (fee, active miners, online status) that propagates across nodes.

## Wallet CLI

```bash
helix-wallet
```

Run `help` inside the wallet. Wallet history is paginated by the node to prevent very large responses.

## Maintenance

```bash
helixctl status
helixctl validate
helixctl backup
helixctl compact
```

Always stop the node before manually compacting or copying its database. `helixctl backup` creates a timestamped copy in `backups/` by default.

## Custom tokens in 1.0.0

The browser wallet can create, discover, mint, transfer, buy, and sell custom tokens using a model inspired by Solana's SPL Token Program. Every token has:

- A deterministic **MNT address** that uniquely identifies the mint.
- A **DAD address**, Helix's name for the current management and mint authority.
- On-chain metadata snapshot: name, symbol, description, image URL, decimals,
  metadata URI, and the snapshot's SHA-256 hash.
- A deterministic associated token-account address for each holder/MNT pair.
- Balances, token-account existence, current DAD, and supply reconstructed from confirmed blocks.

A new MNT starts with zero supply, like a new Solana mint. A submitted creation does not exist from the chain's point of view until a miner includes it in a valid block. Only the current DAD can mint. DAD can be transferred to another wallet or permanently revoked; revocation produces a fixed-supply token and cannot be reversed.

The metadata URI must be an HTTPS URL returning JSON with `name`, `symbol`, `description`, and `image` fields. During creation, the browser loads this document and submits a signed snapshot plus a SHA-256 metadata hash. Consensus verifies the snapshot and hash without making blockchain validation depend on an external web server. See `web/token-metadata.example.json`.

The Discover tab lists every confirmed mint, regardless of creator or holder.
The current DAD may create one permanent HLX/token liquidity pool by entering
only the HLX contribution; consensus automatically requires the DAD wallet's
entire confirmed token balance as the paired reserve. Once mined,
any wallet can buy or sell through a constant-product market with a 0.3% fee
retained in the pool. Buys raise the reserve price and sells lower it; signed
swaps include a minimum received amount for slippage protection.
Tokens with active pools can also be swapped directly. Consensus atomically
sells the source token into its HLX pool and spends that routed HLX value in the
target pool. Both 0.3% pool fees apply, and the wallet never holds the
intermediate HLX during the transaction.
Pool liquidity is reported as the amount of HLX currently locked in the pool;
the token reserve remains part of the constant-product price calculation.

Token API routes include `GET /tokens`, `GET /token/{mint_address}`, `GET /dad/{dad_address}/tokens`, balance and history lookups, plus the existing signed `POST /transaction` endpoint for `token_create`, `token_mint`, `token_burn`, `token_transfer`, `token_set_authority`, `token_pool_create`, `token_pool_add_hlx`, `token_buy`, `token_sell`, and `token_swap` operations. `GET /transactions/recent` supplies the paginated, clickable, network-wide Activity feed.

An unconfirmed transaction can be removed with the signed
`POST /transaction/{tx_id}/cancel` endpoint. The sender's secp256k1 proof is
required, cancellation tombstones survive restarts for the mempool TTL, and
peers relay the proof so the same transaction is not immediately reintroduced.

Helix does not claim wire compatibility with Solana. In Solana terminology, DAD maps most closely to the mint authority. Solana also supports separate freeze and metadata-update authorities; those are intentionally not combined into the current Helix consensus rules.

This release uses peer protocol version 14. The chain has been relaunched from a fresh genesis with every rule active from block 1: a flat 10 HLX reward per block, fine-grained difficulty seeded at 5.5 retargeting every 100 blocks toward a 10-minute average (first retarget at block 101, no reset height), and tokens, liquidity pools, atomic token-to-token swaps, NFTs, the NFT marketplace, and the native HLX DAD identity all active from block 1. Consensus caps the total native supply at 20,000,000 HLX. Signed transaction fees and canonical low-S signatures become mandatory at block 200. Every node must upgrade; earlier protocol versions are intentionally incompatible.

From block 1, `9d7c721b209cee99a8158c524fa433ead9236781` is
the protocol-defined native HLX DAD governance identity. It has no mint power:
all new HLX remains mining-only, the reward remains consensus-controlled,
and the DAD cannot bypass or raise the 20,000,000 HLX cap. The token metadata
snapshot rule, the token exchange, atomic swaps, and signed NFT mint, transfer,
listing, escrowed bidding, purchase, and royalty settlement are all
active from block 1 as well.

## Performance improvements in 0.7.0

- In-memory balance index
- Constant-time confirmed transaction lookup
- Per-address confirmed transaction history index
- Paginated wallet history responses
- Bounded API page sizes
- Health endpoint for service monitoring
- Compact database maintenance command

The full chain remains stored because unsafe deletion of historical blocks would break validation. Safe cryptographic pruning requires a snapshot/state-root design and is intentionally not pretended here.

## Important configuration

When Cloudflared proxies into the node over loopback, Helix trusts
`CF-Connecting-IP`/`X-Forwarded-For` only from that loopback connection so
visitors receive separate rate-limit buckets. Forwarded client headers from
non-loopback clients are ignored. Restart the node after changing this setting;
temporary bans are persisted in `security_state.json`.

`config.json` contains node, network, blockchain, mempool, wallet, security, and performance settings. The admin API key is **optional by default** (`require_admin_api_key: false`), so a plain node needs no key. Before exposing a node publicly:

- Enable TLS.
- Turn the admin key on: set `HELIX_REQUIRE_ADMIN_API_KEY=true` and a long random
  `HELIX_ADMIN_API_KEY` before starting the node.
- If you host the Pages wallet in front of it, set the exact same value as the
  encrypted `HELIX_ADMIN_API_KEY` secret in Cloudflare Pages. Never put the key
  inside the `web` folder.
- Configure a public URL and trusted bootstrap nodes.
- Back up wallet and database files.

## Project layout

```text
node/             blockchain, P2P networking, consensus, security, pool registry
wallet/           wallet implementation and CLI
web/              browser wallet and Cloudflare Pages deployment package
config.json       runtime settings
run_node.py       node launcher
run_pool.py       mining-pool launcher
pool_server.py    mining-pool coordinator (shares, payouts, stats)
helix_miner.py    desktop miner (CPU/NVIDIA, solo/pool)
miner_cuda.py     optional NVIDIA CUDA backend
install_node.py   GUI node installer (setup.bat)
start-node.bat    one-click node setup/launch (Windows)
start-node.sh     one-click node setup/launch (Linux/macOS)
helixctl.py       local maintenance utility
```

See `web/README.md` to deploy the browser wallet to Cloudflare Pages.

## License

Released under the [MIT License](LICENSE) — free to use, modify, and distribute,
provided the copyright notice is kept. The software is provided "as is" without
warranty; Helix is an educational project and has not been audited, so do not
use it to protect real money.
