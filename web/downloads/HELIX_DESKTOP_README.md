# Helix Desktop Apps

## Windows

- `HelixWallet.exe` opens `https://wallet.hlxchain.com/` in a dedicated
  Edge/Chrome app window. It is the same non-custodial wallet website.
- `HelixMiner.exe` is the CPU-capable packaged miner. Use the Python miner
  download for NVIDIA CUDA because CuPy and CUDA are driver-specific and much
  too large for one universal executable.
- Extract the complete `helix-node.zip`, then run `HelixNodeSetup.exe` from its
  extracted root. Python 3.11+ is still required because the installer creates
  the node environment and installs server dependencies.

Windows may show SmartScreen because these community-built executables are not
code-signed. Verify their published SHA-256 checksums before running them.

## Linux

Open the `linux-wallet` folder in a terminal and run:

```sh
chmod +x helix-wallet install-helix-wallet.sh
./install-helix-wallet.sh
```

This installs a standard `.desktop` launcher. Linux miner and node software is
provided in `helix-miner.zip` and `helix-node.zip`; those remain Python programs
so they work across distributions without an unsafe cross-compiled binary.
