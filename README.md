# Helix Coin 1.0.0

Helix is an educational proof-of-work cryptocurrency project with encrypted wallets, custom tokens, peer discovery, mempool gossip, block relay, fork handling, checkpoints, dynamic difficulty, and network hardening.  

## Updates

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
every 10 blocks toward a **10-minute** average block time. Each adjustment scales
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

Before block 161, the historical dynamic-difficulty rules remain part of chain
validation. Block 161 receives a one-time reset to difficulty 3. Blocks 161
through 170 stay at 3 so the network can collect one complete post-reset
window. Beginning with block 171, difficulty can move by one hexadecimal step
every 10 blocks: it rises when the window average is below 80 seconds and falls
when the average is above 160 seconds. The target is probabilistic, so an
individual block can take more or less than 160 seconds.

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
(share difficulty = network difficulty minus this, default 2), `HELIX_POOL_PORT`
(default 8100). Expose port 8100 with its own tunnel and share that URL with
miners. Block templates are addressed to the pool wallet; when a member solves a
block the reward is split proportionally to each miner's shares and paid out
on-chain, with the fee kept by the operator. Payouts are whole HLX, so a 1% fee
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

This release uses peer protocol version 10. All nodes participating in the same network must upgrade and restart before mining or accepting block 200, when atomic token swaps activate. The historical difficulty reset occurred at block 161, difficulty stayed at 3 through block 170, and automatic 10-block adjustment resumed at block 171 using a 160-second target. Prior blocks are not rewritten. Blocks 0 through 89 retain their historical 10 HLX reward, blocks 90 through 299 pay 2 HLX, and block 300 onward pays 10 HLX. Consensus caps the total native supply at 20,000,000 HLX.

At block 300, `9d7c721b209cee99a8158c524fa433ead9236781` becomes
the protocol-defined native HLX DAD governance identity. It has no mint power:
all new HLX remains mining-only, the reward schedule remains consensus-controlled,
and the DAD cannot bypass or raise the 20,000,000 HLX cap. This activation does
not rewrite or reset historical blocks.
On the existing mainnet chain, the metadata snapshot rule activates at block 41;
the token exchange activates at block 41, and the earlier SLOP mint remains valid
with its original block hash.

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
