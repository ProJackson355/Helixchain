# Helix — feature roadmap

Priority order (build top to bottom):

1. **Payment-request QR + shareable link** — QR/deep link carries `?to=&amount=`,
   pre-fills recipient *and* amount on the Send tab. The link also renders a rich
   preview in iOS Messages / social (Open Graph tags injected by the Worker) so it
   shows the requested amount.
2. **Confirmation / finality counter** — show "N confirmations" on transactions
   (current height − tx block height); treat as final after a threshold.
3. **Address book** — save labeled contacts locally (non-custodial), pick a
   recipient from a dropdown instead of pasting 40 hex chars.
4. **Auto-checkpoints** — the node pins its own chain every N blocks (local
   finality) using the existing checkpoint enforcement in `replace_chain`, capping
   reorg depth.
5. **Tx-confirmed notifications** — PWA Notifications API alerts when a pending
   transaction confirms.
6. **Cached `chain_work` / incremental audit** — stop recomputing work O(n²);
   cache per-block work so the chain scales to more nodes / longer history.
7. **In-app QR scanner** — scan a receive code inside the wallet (camera → decode →
   fill Send). Needs relaxing the `camera=()` Permissions-Policy.
8. **NFTs** — modeled on Solana-style mints (supply 1, 0 decimals, metadata).
   - **Stage A (core):** mint an NFT (name/description/image via URI+hash),
     on-chain ownership, transfer between wallets, gallery of owned NFTs.
     Reuses the existing token consensus (adds an `is_nft` flag + "max supply 1 /
     no re-mint" rule) — low risk.
   - **Stage B (marketplace):** list an NFT for sale and trade it for HLX, a
     fungible token, OR another NFT — atomic escrow-style swap. Larger consensus
     change; build after Stage A is solid. Standalone NFTs (no collections) for MVP.

9. **Mobile safe-area fix** — the top header rode up under the iOS Dynamic Island /
   status bar (because the PWA uses a translucent status bar). Pad the header and
   the mobile nav panel down by `env(safe-area-inset-top)`.

Status: 1–7 done and verified; 9 done; 8 Stage A (core NFTs) done and verified;
8 Stage B (NFT marketplace: trade for HLX / token / another NFT) queued.
