# Helix Wallet on Cloudflare Pages

This directory is the complete Cloudflare Pages deployment package. Upload this
directory as the Pages asset folder; do not upload the blockchain database,
Python source, wallet files, or node configuration.

## What is included

- `index.html` — browser wallet page.
- `app.js` — browser wallet application logic. The page will not work if this
  file is omitted from an upload.
- `_worker.js` — same-origin `/api/*` gateway to your Helix node.
- `_headers` — browser security and cache headers.
- `token-metadata.example.json` — metadata-file template using the required
  `name`, `symbol`, `description`, and HTTPS `image` fields.
- `downloads/helix-miner.zip` and `downloads/helix-node.zip` - downloadable
  Python software bundles linked from the public Docs tab.

The **Activity** tab provides numbered pages of confirmed transactions across
every wallet, newest first. The personal **History** tab remains scoped to the
unlocked wallet. Selecting any Activity row opens its complete transaction and
block details.

The wallet includes the custom-token interface. Token definitions and balances
come from the node's confirmed blockchain state; a newly submitted token will
appear after its creation transaction is mined. Each token has an MNT identifier
and a DAD management authority. New mints begin with zero supply; DAD can mint,
transfer authority to another wallet, or permanently revoke authority.

The dashboard and **My Tokens** view show every token with a confirmed balance
in the active wallet, regardless of who created it or controls its DAD. The
separate **Management** view also includes zero-balance tokens controlled by the
wallet's DAD authority. Token creation has its own **Create Token** view, with a
direct create option whenever the wallet has no token balances.

The **Discover** view lists every confirmed token, including tokens made by
other wallets. Selecting one shows its metadata, MNT, DAD, supply, wallet
balance, pool reserves, and current price. A DAD can seed one permanent
HLX/token exchange pool from Management. Pool creation asks only for HLX and
automatically deposits the DAD wallet's entire confirmed token balance as the
paired reserve, so the DAD cannot manually choose a token-liquidity amount.
Anyone can then buy or sell through
constant-product pricing; the pool retains a 0.3% fee and the wallet submits a
minimum output with each trade to limit slippage. These markets are experimental
and are not a promise that a token has value or sufficient liquidity.
Discovery reports and ranks liquidity by the pool's locked HLX amount. Buys add
HLX liquidity and sells remove it, while the paired token reserve is retained
for deterministic price and output calculations.
HLX itself appears as the native asset in Discover. The current DAD also has an
**Add HLX Liquidity** action for an active pool; this permanently moves HLX into
the pool without removing tokens and therefore raises its reserve price.

Before creating a token, upload a metadata JSON file to an HTTPS host such as an
IPFS gateway. Paste that JSON file's URL—not the image URL—into the wallet. The
wallet previews the document and commits its four core fields and SHA-256 hash
to the confirmed token-creation transaction.

Token cards and detail views display the metadata document's `image`. For
pre-snapshot token blocks that only contain a metadata URI, the wallet fetches
and caches that JSON as a display fallback, but only accepts it when its name
and symbol match the confirmed on-chain mint identity.

The package intentionally does not include `_routes.json`. Some Cloudflare
dashboard upload flows reject that file. Advanced-mode `_worker.js` already
proxies only `/api/*` and sends every other request to the Pages static asset
service with `env.ASSETS.fetch(request)`.

The gateway is necessary because a Pages site uses HTTPS. A browser cannot call
an ordinary `http://` node from an HTTPS page, and Cloudflare Pages `_redirects`
cannot proxy an external domain.

## Before deployment

Your Helix node must be reachable from Cloudflare at a public URL. `localhost`
and `127.0.0.1` refer to Cloudflare's servers and will not work. Use an HTTPS
reverse proxy or a Cloudflare Tunnel in front of the node. Do not expose a node
holding real funds; Helix is an educational network and has not been audited.

If a TryCloudflare URL returns `Client temporarily banned` for every request,
restart the node after enabling `security.trust_loopback_proxy_headers`. This
lets Helix use Cloudflare's client IP only when Cloudflared is connected from
loopback, preventing the tunnel itself (`127.0.0.1`) from consuming one shared
rate-limit bucket. The Pages Worker also sends the original visitor address in
an authenticated internal header so Cloudflare's shared Worker address is not
banned on behalf of every visitor.

In the Cloudflare dashboard, open your Pages project and go to
**Settings > Variables and Secrets**. Add:

- `HELIX_NODE_URL` — required. Set either one public node URL, such as
  `https://node.example.com`, or a JSON array ordered from primary to fallback:

  ```json
  ["https://node1.example.com", "https://node2.example.com"]
  ```

  The gateway accepts the array as dashboard text or a JSON binding, removes
  duplicates, and supports up to 10 nodes. Read requests and signed
  `/transaction` submissions fail over on connection errors or 5xx responses.
  Mining and other administrative writes use only one selected node to prevent
  an uncertain response from executing an action twice. Before choosing that
  node, the gateway probes configured nodes in order and skips dead entries.
  Remove expired TryCloudflare URLs anyway; they are temporary. Every configured
  node must run the same Helix network and protocol and should stay synchronized.
- `HELIX_ADMIN_API_KEY` — required for mining and other administrative web
  actions. Choose **Encrypt** and use the exact same long random value supplied
  to the local node's `HELIX_ADMIN_API_KEY` environment variable. Never place
  this secret in any file in the `web` folder.
- `HELIX_ENABLE_ADMIN_API` — optional variable. Set it to the exact string
  `true` to enable mining, peer registration, discovery, audit, and manual sync
  through the public site. These routes are disabled by default.

Redeploy after adding or changing variables.

## Deploy by drag and drop

1. In Cloudflare, open **Workers & Pages**.
2. Select **Create application > Get started > Drag and drop your files**.
3. Enter a project name.
4. Drag the entire `web` folder into the upload area and deploy it.
   Confirm the upload contains `index.html`, `app.js`, `_worker.js`, and
   `_headers`; uploading only `index.html` leaves the page without JavaScript.
5. Add the variables above, then create a new deployment so they take effect.
6. Open `https://YOUR_PROJECT.pages.dev/api/health`. It should return node
   health JSON.
7. Open the wallet's **Tokens** tab to create, mint, or transfer custom tokens.
   The Pages gateway forwards these signed requests through the same
   `HELIX_NODE_URL` binding.

Cloudflare supports `_worker.js` in dashboard drag-and-drop deployments. A
`functions/` directory would require Wrangler instead, which is why this package
uses advanced-mode `_worker.js`. If the upload mentions unsupported special
files, make sure you selected **Workers & Pages > Create application > Pages >
Drag and drop** rather than a Workers static-assets upload.

## Deploy with Wrangler

From the Helixchain project directory:

```powershell
npx wrangler pages deploy web --project-name=helixchain
```

For a Git-connected Pages project, use no build command and set the build output
directory to `web`.

## Local use

Running the Python node still serves this same UI at `http://127.0.0.1:8000/`.
For a local Cloudflare gateway preview, install Wrangler and run:

```powershell
npx wrangler pages dev web --binding HELIX_NODE_URL=http://127.0.0.1:8000 --binding HELIX_ENABLE_ADMIN_API=true
```

## Security notes

- The unlock screen accepts a typed wallet name and password; it does not list
  locally stored wallet names in a dropdown.
- Wallets are encrypted in browser `localStorage`. An unlocked private key is
  kept in tab-scoped `sessionStorage` for up to one hour so refreshes remain
  logged in. Locking the wallet clears it immediately.
- The dashboard can delete the active wallet's encrypted local record after
  password verification and a separate confirmation. Deletion clears its
  active session but does not delete blockchain funds; restoring access
  requires the wallet's seed phrase.
- The web wallet does not provide server-side user authentication. Enabling
  `HELIX_ENABLE_ADMIN_API` makes those selected administrative actions publicly
  callable through the Pages URL. Enable it only when that is intentional.
- Keep the node's rate limits enabled and restrict its origin firewall so only
  the intended proxy or tunnel can reach it.

Cloudflare references:

- https://developers.cloudflare.com/pages/get-started/direct-upload/
- https://developers.cloudflare.com/pages/functions/advanced-mode/
- https://developers.cloudflare.com/pages/functions/routing/
- https://developers.cloudflare.com/pages/functions/bindings/
