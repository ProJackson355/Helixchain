# Helix Pool

Helix Pool combines miners' hashrate and divides each confirmed block payment
using each miner's weighted work in a rolling PPLNS share window.

## Requirements

- Python 3.11 or newer. On Linux, install the OS `python3-tk` package if the GUI
  is unavailable.
- A reachable protocol-15 Helix node.
- A dedicated 12-word Helix wallet seed for receiving block payments and paying
  miners. Back it up securely and keep enough HLX available for payout fees.
- Optional: `cloudflared` on `PATH` for a public pool URL.

## GUI setup

1. Windows: double-click `setup-pool.bat`. Linux/macOS: run
   `bash start-pool.sh` or `python3 install_pool.py`.
2. Enter the dedicated pool payout wallet's 12-word seed and select where the
   wallet was created. Choose **Helix website wallet** for a wallet made at
   wallet.hlxchain.com (the default), or **Python/CLI BIP-39 wallet** for one
   made by the Python wallet tools. These formats derive different addresses.
   The GUI keeps the seed in memory and never writes it to settings or logs.
3. Enter one or more Helix node URLs, separated by commas. The first is used for
   work; solved blocks and payouts fail over across the list.
4. Choose the pool port, operator fee, share-difficulty reduction, and minimum
   share difficulty. The defaults are suitable for initial testing.
5. Select **Set Up & Start Pool**. The first launch creates `.venv` and installs
   the included requirements.
6. Give miners the pool's public base URL. They choose **Pool** mode in Helix
   Miner and enter that URL plus their own reward address.

The **Status & Logs** tab shows the current height, pool and network difficulty,
round shares, estimated hashrate, miners, blocks found, and total payouts.

## Cloudflare tunnel token

The GUI supports either tunnel type:

- **Named tunnel:** paste the tunnel token into the masked Cloudflare token
  input. In Cloudflare Zero Trust, configure that tunnel's public hostname to
  use service `http://localhost:8100` (replace `8100` if you changed the port).
  The GUI runs `cloudflared tunnel run --token TOKEN`. The token is not saved or
  printed.
- **Temporary tunnel:** leave the token blank and enable the temporary-tunnel
  checkbox. The GUI runs `cloudflared tunnel --url http://localhost:8100`, shows
  the generated `https://...trycloudflare.com` URL, and copies it to the
  clipboard. This URL changes whenever the tunnel restarts.

For a named tunnel, enter/list its configured public hostname in the wallet's
Pools tab. A token does not reveal the hostname to the GUI, so it cannot infer
that URL automatically.

## Manual setup

Copy `pool.env.example` values into your terminal environment, replace the seed,
set `HELIX_POOL_SEED_FORMAT=web` for a website wallet or `bip39` for a Python
wallet, install `requirements.txt`, and run `python run_pool.py`. The API is available
at `/pool/info`, `/pool/work`, `/pool/submit`, and `/pool/stats`.

Never publish the seed phrase, Cloudflare token, `.venv`, or local settings.
Pool payouts are whole-HLX transactions and each payout pays the network fee.
The pool adjusts share difficulty per miner toward one accepted share every 15
seconds by default. Configure `HELIX_POOL_PPLNS_WINDOW` and
`HELIX_POOL_SHARE_SECONDS` to change the payout window and vardiff target.
