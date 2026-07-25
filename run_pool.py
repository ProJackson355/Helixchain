"""Launch a Helix mining pool coordinator.

Set at least a pool wallet before starting so the pool can pay miners:

  set HELIX_POOL_SEED=word word word ... (12 words)   # Windows
  export HELIX_POOL_SEED="word word word ..."          # Linux/macOS

Other optional settings: HELIX_POOL_NODE, HELIX_POOL_FEE_PERCENT,
HELIX_POOL_SHARE_SUBTRACT, HELIX_POOL_HOST, HELIX_POOL_PORT.
"""
from __future__ import annotations

import os
import uvicorn


def main():
    host = os.getenv("HELIX_POOL_HOST", "0.0.0.0")
    port = int(os.getenv("HELIX_POOL_PORT", "8100"))
    if not os.getenv("HELIX_POOL_SEED") and not os.getenv("HELIX_POOL_ADDRESS"):
        print("WARNING: set HELIX_POOL_SEED (or HELIX_POOL_ADDRESS) so the pool has a payout wallet. "
              "Without a seed the pool tracks shares but cannot send payouts.")
    uvicorn.run(
        "pool_server:app",
        host=host,
        port=port,
        server_header=False,
        date_header=False,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
