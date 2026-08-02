# Helix Node

Requirements: Python 3.11 or newer.

## GUI setup

1. Windows: extract the complete ZIP and run `HelixNodeSetup.exe` (or
   `setup.bat`). The EXE is the setup GUI; it still needs an installed Python
   3.11+ to create the node environment. Linux/macOS: run
   `bash start-node.sh --gui` or `python3 install_node.py`.
2. Choose the node port, public URL, bootstrap nodes, and optional admin API
   protection.
3. To start a named Cloudflare tunnel, paste its token into the masked
   **Cloudflare named-tunnel token** input. The token is passed directly to
   `cloudflared tunnel run --token TOKEN`; it is never saved in `config.json`.
4. In Cloudflare Zero Trust, configure the tunnel's public hostname service as
   `http://localhost:8000` (replace `8000` if you changed the node port), and put
   that hostname in the GUI's Public URL field.
5. If the token input is blank, selecting the tunnel option creates a temporary
   `trycloudflare.com` URL instead. Temporary URLs change after a restart.
6. Select **Set Up & Start Node**, then verify the local `/health` endpoint.

## Manual setup

1. Create an environment: `python -m venv .venv`.
2. Install dependencies: `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
3. Start: `.venv\Scripts\python.exe run_node.py`.
4. Verify: open `http://127.0.0.1:8000/health`.

On Linux or macOS, use `.venv/bin/python`. Configure bootstrap nodes, public
URL, ports, security, and consensus compatibility in `config.json`.

The admin API key is optional by default. When exposing administrative routes,
set a persistent `HELIX_ADMIN_API_KEY` and enable the requirement. Different
operators can use different keys because the key is local access control, not
blockchain consensus data.

The node does not perform proof-of-work, even for an administrator. It only
provides block templates at `GET /mining/work` and validates externally solved
blocks at `POST /mining/submit`. Use Helix Miner on your own CPU or NVIDIA GPU.

Before exposing a node, use TLS or a secure tunnel, retain rate limits, use a
firewall, and back up the database. All participating nodes must use compatible
peer protocol 15 and matching consensus settings. Canonical transaction
signatures and the signed transaction fee become mandatory at block 200.
Replay-protected transaction envelopes plus Merkle/state commitments become
mandatory at block 1000. On first protocol-15 start, the validated JSON database
is imported into `database_PORT.sqlite3`; back up both files. Monitor
`/health/details` and `/metrics` in addition to `/health`.
