# Helix Node

Requirements: Python 3.11 or newer.

1. Create an environment: `python -m venv .venv`
2. Install dependencies: `.venv\Scripts\python.exe -m pip install -r requirements.txt`
3. Set a persistent `HELIX_ADMIN_API_KEY` in the terminal or service that starts
   the node. Keep the value private and reuse it after restarts.
4. Start: `.venv\Scripts\python.exe run_node.py`
5. Verify: open `http://127.0.0.1:8000/health`.

When using a temporary Cloudflare tunnel, first verify
`https://YOUR-URL.trycloudflare.com/health`, then email the working
TryCloudflare URL to `jackson.tripp100@gmail.com` so it can be considered for
the Helix node list. TryCloudflare addresses expire when their tunnel stops, so
send an updated URL after restarting the tunnel.

On Linux or macOS, use `.venv/bin/python` instead. Configure bootstrap nodes,
public URL, ports, security, and consensus compatibility in `config.json`.
Different operators can use different admin API keys because the key protects
local administrative routes and is not blockchain consensus data.

Before exposing a node, enable TLS or a secure tunnel, retain rate limits, use a
firewall, and back up the database. All nodes participating in the same network
must run compatible protocol and consensus settings.

## Reward protocol

Protocol 10 preserves the one-time mining-difficulty reset at block 161 and
activates atomic token-to-token swaps routed through HLX liquidity pools at
block 200.
Difficulty remains 3 through block 170, then automatic adjustment resumes at
block 171 after the first complete post-reset window. Historical blocks keep
the proof requirements under which they were mined. Every node must upgrade
and restart before mining or accepting block 200.

The 10 HLX reward returns at block 300. Historical blocks 0-89
remain at 10 HLX and blocks 90-299 remain at 2 HLX. Upgrade and restart every
participating node before height 300.

At block 161, the adaptive target changes from 600 seconds to 160 seconds per
block. After the reset window, difficulty is evaluated every 10 blocks, rises
when the window average is below 80 seconds, and falls when it is above 160
seconds. Block discovery remains probabilistic, so individual blocks may be
faster or slower than the target.

At block 300, `9d7c721b209cee99a8158c524fa433ead9236781` becomes
the native HLX DAD governance identity. It is explicitly non-minting: it cannot
create HLX, change proof-of-work rewards, or bypass the maximum supply. No chain
reset is required.
