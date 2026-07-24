"""Optional NVIDIA CUDA SHA-256 backend for Helix Miner.

CuPy is imported lazily so the normal CPU miner keeps working without CUDA.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import time


CUDA_SOURCE = r'''
extern "C" {
typedef struct {
    unsigned int state[8];
    unsigned char block[64];
    unsigned int used;
    unsigned long long total;
} Sha256Ctx;

__device__ __forceinline__ unsigned int rotr(unsigned int x, unsigned int n) {
    return (x >> n) | (x << (32 - n));
}

__device__ void transform(Sha256Ctx *ctx) {
    const unsigned int k[64] = {
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    };
    unsigned int w[64];
    for (int i = 0; i < 16; ++i) {
        int j = i * 4;
        w[i] = ((unsigned int)ctx->block[j] << 24) | ((unsigned int)ctx->block[j+1] << 16)
             | ((unsigned int)ctx->block[j+2] << 8) | (unsigned int)ctx->block[j+3];
    }
    for (int i = 16; i < 64; ++i) {
        unsigned int s0 = rotr(w[i-15],7) ^ rotr(w[i-15],18) ^ (w[i-15] >> 3);
        unsigned int s1 = rotr(w[i-2],17) ^ rotr(w[i-2],19) ^ (w[i-2] >> 10);
        w[i] = w[i-16] + s0 + w[i-7] + s1;
    }
    unsigned int a=ctx->state[0], b=ctx->state[1], c=ctx->state[2], d=ctx->state[3];
    unsigned int e=ctx->state[4], f=ctx->state[5], g=ctx->state[6], h=ctx->state[7];
    for (int i = 0; i < 64; ++i) {
        unsigned int s1 = rotr(e,6) ^ rotr(e,11) ^ rotr(e,25);
        unsigned int ch = (e & f) ^ ((~e) & g);
        unsigned int t1 = h + s1 + ch + k[i] + w[i];
        unsigned int s0 = rotr(a,2) ^ rotr(a,13) ^ rotr(a,22);
        unsigned int maj = (a & b) ^ (a & c) ^ (b & c);
        unsigned int t2 = s0 + maj;
        h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }
    ctx->state[0]+=a; ctx->state[1]+=b; ctx->state[2]+=c; ctx->state[3]+=d;
    ctx->state[4]+=e; ctx->state[5]+=f; ctx->state[6]+=g; ctx->state[7]+=h;
}

__device__ __forceinline__ void update_byte(Sha256Ctx *ctx, unsigned char value) {
    ctx->block[ctx->used++] = value;
    ctx->total++;
    if (ctx->used == 64) { transform(ctx); ctx->used = 0; }
}

__device__ void finish(Sha256Ctx *ctx) {
    unsigned long long bits = ctx->total * 8ULL;
    ctx->block[ctx->used++] = 0x80;
    if (ctx->used > 56) {
        while (ctx->used < 64) ctx->block[ctx->used++] = 0;
        transform(ctx); ctx->used = 0;
    }
    while (ctx->used < 56) ctx->block[ctx->used++] = 0;
    for (int shift = 56; shift >= 0; shift -= 8) ctx->block[ctx->used++] = (unsigned char)(bits >> shift);
    transform(ctx);
}

__global__ void mine_sha256(
    const unsigned char *prefix, unsigned int prefix_len,
    const unsigned char *suffix, unsigned int suffix_len,
    unsigned long long start_nonce, unsigned long long count,
    unsigned int difficulty, unsigned long long *result_nonce, int *found
) {
    unsigned long long offset = (unsigned long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (offset >= count || *found) return;
    unsigned long long nonce = start_nonce + offset;
    if (nonce < start_nonce) return;
    Sha256Ctx ctx;
    ctx.state[0]=0x6a09e667; ctx.state[1]=0xbb67ae85; ctx.state[2]=0x3c6ef372; ctx.state[3]=0xa54ff53a;
    ctx.state[4]=0x510e527f; ctx.state[5]=0x9b05688c; ctx.state[6]=0x1f83d9ab; ctx.state[7]=0x5be0cd19;
    ctx.used=0; ctx.total=0;
    for (unsigned int i=0; i<prefix_len; ++i) update_byte(&ctx, prefix[i]);
    unsigned char digits[20];
    int digit_count=0;
    unsigned long long value=nonce;
    do { digits[digit_count++] = (unsigned char)('0' + value % 10ULL); value /= 10ULL; } while (value);
    for (int i=digit_count-1; i>=0; --i) update_byte(&ctx, digits[i]);
    for (unsigned int i=0; i<suffix_len; ++i) update_byte(&ctx, suffix[i]);
    finish(&ctx);
    bool valid = difficulty <= 64;
    for (unsigned int nibble=0; valid && nibble<difficulty; ++nibble) {
        unsigned int word = ctx.state[nibble / 8];
        unsigned int shift = 28 - (nibble % 8) * 4;
        if (((word >> shift) & 0xf) != 0) valid = false;
    }
    if (valid && atomicCAS(found, 0, 1) == 0) *result_nonce = nonce;
}
}
'''


def canonical_block_parts(block: dict) -> tuple[bytes, bytes]:
    """Split canonical block JSON immediately before its numeric nonce value."""
    candidate = deepcopy(block)
    candidate["nonce"] = 0
    candidate.pop("hash", None)
    encoded = json.dumps(
        candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    marker = b'"nonce":0'
    if encoded.count(marker) != 1:
        raise ValueError("Could not isolate the canonical block nonce")
    before, after = encoded.split(marker, 1)
    return before + b'"nonce":', after


def canonical_block_hash(block: dict, nonce: int) -> str:
    prefix, suffix = canonical_block_parts(block)
    return hashlib.sha256(prefix + str(nonce).encode("ascii") + suffix).hexdigest()


class NvidiaCudaMiner:
    """Compile and run Helix's SHA-256 nonce search on one NVIDIA GPU."""

    THREADS_PER_BLOCK = 256
    DEFAULT_BATCH_SIZE = 1 << 22

    def __init__(self, device_id: int = 0):
        try:
            import cupy as cp
        except ImportError as exc:
            raise RuntimeError(
                "NVIDIA mode requires CuPy. Install cupy-cuda13x[ctk] for CUDA 13 "
                "or cupy-cuda12x[ctk] for CUDA 12."
            ) from exc
        self.cp = cp
        try:
            count = cp.cuda.runtime.getDeviceCount()
            if count <= device_id:
                raise RuntimeError("No compatible NVIDIA CUDA GPU was detected.")
            self.device = cp.cuda.Device(device_id)
            self.device.use()
            properties = cp.cuda.runtime.getDeviceProperties(device_id)
            name = properties.get("name", properties.get(b"name", b"NVIDIA CUDA GPU"))
            self.device_name = name.decode(errors="replace") if isinstance(name, bytes) else str(name)
            self.kernel = cp.RawKernel(CUDA_SOURCE, "mine_sha256", options=("--std=c++11",))
            self.result_nonce = cp.zeros(1, dtype=cp.uint64)
            self.found = cp.zeros(1, dtype=cp.int32)
        except Exception as exc:
            raise RuntimeError(f"CUDA initialization failed: {exc}") from exc
        self.block = None
        self.difficulty = 0
        self.prefix = None
        self.suffix = None

    def prepare(self, block: dict, difficulty: int) -> None:
        if not 0 <= int(difficulty) <= 64:
            raise ValueError("Difficulty must be between 0 and 64 hexadecimal digits.")
        prefix, suffix = canonical_block_parts(block)
        self.block = deepcopy(block)
        self.difficulty = int(difficulty)
        self.prefix = self.cp.asarray(bytearray(prefix), dtype=self.cp.uint8)
        self.suffix = self.cp.asarray(bytearray(suffix), dtype=self.cp.uint8)

    def mine_batch(self, start_nonce: int, count: int | None = None) -> tuple[dict | None, int, float]:
        if self.block is None:
            raise RuntimeError("CUDA work has not been prepared")
        count = int(count or self.DEFAULT_BATCH_SIZE)
        self.found.fill(0)
        self.result_nonce.fill(0)
        blocks = (count + self.THREADS_PER_BLOCK - 1) // self.THREADS_PER_BLOCK
        started = time.monotonic()
        self.kernel(
            (blocks,), (self.THREADS_PER_BLOCK,),
            (
                self.prefix, self.cp.uint32(self.prefix.size),
                self.suffix, self.cp.uint32(self.suffix.size),
                self.cp.uint64(start_nonce), self.cp.uint64(count),
                self.cp.uint32(self.difficulty), self.result_nonce, self.found,
            ),
        )
        self.cp.cuda.runtime.deviceSynchronize()
        elapsed = time.monotonic() - started
        if int(self.found.get()[0]) == 0:
            return None, count, elapsed
        nonce = int(self.result_nonce.get()[0])
        digest = canonical_block_hash(self.block, nonce)
        if not digest.startswith("0" * self.difficulty):
            raise RuntimeError("CUDA returned a proof that failed CPU consensus verification")
        solved = deepcopy(self.block)
        solved["nonce"] = nonce
        solved["hash"] = digest
        return solved, count, elapsed
