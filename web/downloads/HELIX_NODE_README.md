# Helix Node

Requirements: Python 3.11 or newer.

## GUI setup

1. Windows: double-click `setup.bat`. Linux/macOS: run
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

Before exposing a node, use TLS or a secure tunnel, retain rate limits, use a
firewall, and back up the database. All participating nodes must use compatible
peer protocol 14 and matching consensus settings. Canonical transaction
signatures and the signed transaction fee become mandatory at block 200.
