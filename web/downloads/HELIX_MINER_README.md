# Helix Miner

Requirements: Python 3.11 or newer and a reachable Helix node.

1. Install dependencies: `python -m pip install -r requirements.txt`
2. Launch: `python helix_miner.py`
3. Enter a 40-character Helix reward address and one or more node URLs.
4. Choose the number of worker processes and start mining.

## NVIDIA CUDA

For an NVIDIA GPU with a CUDA 13 driver:

`python -m pip install -r requirements-nvidia.txt`

For a CUDA 12 driver, install `cupy-cuda12x[ctk]` instead. Do not install both
CuPy variants. Select **NVIDIA CUDA** under Mining device, or launch with
`python helix_miner.py --backend nvidia`. The GPU searches nonces, and Helix
rechecks every discovered proof with the CPU consensus hash before submission.

### Supported GPUs

- NVIDIA CUDA-capable GPUs with compute capability 3.0 or newer, when the
  selected CUDA runtime and installed NVIDIA driver support the card.
- Typical compatible families include modern GeForce RTX, NVIDIA RTX/Quadro,
  Tesla, and NVIDIA data-center cards. Helix has been hardware-tested on an
  RTX 4050 Laptop GPU.
- CUDA 13 uses `cupy-cuda13x[ctk]`; CUDA 12 uses `cupy-cuda12x[ctk]`. Run
  `nvidia-smi` to see the CUDA version reported by the driver.
- Official CuPy wheels support Windows and Linux. Helix currently uses the
  first detected NVIDIA GPU only; simultaneous multi-GPU mining is not yet
  implemented.
- AMD, Intel, Apple Silicon, and other non-CUDA GPUs are not supported by this
  backend. Use CPU mode on those systems.

An old GPU meeting the minimum compute capability is not automatically
guaranteed to work: its NVIDIA driver and the chosen CUDA 12/13 runtime must
also support that exact card.

The miner uses the public competitive-mining API and does not need an admin API
key. Multiple node URLs can be comma-separated or entered as a JSON array.
It checks the chain tip about once per second. If another miner wins, the app
updates to the new height and starts fresh work; the log shows how long the
completed round took whether this miner or another miner won it.

Difficulty resets once to 3 at block 161 and stays at 3 through block 170.
Beginning with block 171, it adjusts every 10 blocks using a 160-second target:
an average below 80 seconds raises it and an average above 160 seconds lowers
it. Individual solve times vary because proof-of-work is probabilistic.

Helix is educational software and has not received a professional security
audit.
