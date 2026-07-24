# Helix Coin 1.0.0

Helix is an educational proof-of-work cryptocurrency project with encrypted wallets, custom tokens, peer discovery, mempool gossip, block relay, fork handling, checkpoints, dynamic difficulty, and network hardening.

> Helix has not received a professional security audit. Do not use it to protect real money or deploy it as a public financial network without independent review and extensive testing.

## Updates

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
(I actually have no idea if other people can even run a node outside of my local network. In future updates I plan ato buy a domain and use that for the nodes instead of cloudflare for easier peer discovery)  

Download the node software here: [Releases](https://github.com/ProJackson355/Helixchain/releases)
```bash
helix-node
```

Or without installing console commands:

```bash
python run_node.py
```

The default API listens on port `8000`. Edit `config.json` or set environment variables such as `NODE_PORT`, `HELIX_DATABASE`, and `HELIX_CONFIG`.

Health check:

```bash
curl http://127.0.0.1:8000/health
```

If you expose a node with TryCloudflare, verify its public `/health` endpoint
and email the working `trycloudflare.com` URL to
`jackson.tripp100@gmail.com` so it can be considered for the Helix node list.
Temporary TryCloudflare URLs change when the tunnel restarts.

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

Token API routes include `GET /tokens`, `GET /token/{mint_address}`, `GET /dad/{dad_address}/tokens`, balance and history lookups, plus the existing signed `POST /transaction` endpoint for `token_create`, `token_mint`, `token_transfer`, `token_set_authority`, `token_pool_create`, `token_pool_add_hlx`, `token_buy`, `token_sell`, and `token_swap` operations. `GET /transactions/recent` supplies the paginated, clickable, network-wide Activity feed.

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

`config.json` contains node, network, blockchain, mempool, wallet, security, and performance settings. Before exposing a node publicly:

- Enable TLS.
- Keep the administrative API key enabled (it is required by default).
- Set a long random key through `HELIX_ADMIN_API_KEY` before starting the node.
- Set the exact same value as the encrypted `HELIX_ADMIN_API_KEY` secret in
  Cloudflare Pages. Never put the key inside the `web` folder.
- Configure a public URL and trusted bootstrap nodes.
- Back up wallet and database files.

## Project layout

```text
node/           blockchain, P2P networking, consensus, security
wallet/         wallet implementation and CLI
web/            browser wallet and Cloudflare Pages deployment package
config.json     runtime settings
run_node.py     node launcher
helixctl.py     local maintenance utility
```

See `web/README.md` to deploy the browser wallet to Cloudflare Pages.
