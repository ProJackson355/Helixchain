const PUBLIC_ROUTES = [
  ["GET", /^\/(?:chain|pending|nodes|stats|health)$/],
  ["GET", /^\/tokens$/],
  ["GET", /^\/leaderboard$/],
  ["GET", /^\/leaderboard\/[0-9a-f]{40}\/history$/],
  ["GET", /^\/nfts$/],
  ["GET", /^\/nft\/[0-9a-f]{40}$/],
  ["GET", /^\/nft\/[0-9a-f]{40}\/market\/history$/],
  ["GET", /^\/nfts\/owner\/[0-9a-f]{40}$/],
  ["GET", /^\/token\/[0-9a-f]{40}$/],
  ["GET", /^\/token\/[0-9a-f]{40}\/market\/history$/],
  ["GET", /^\/dad\/[0-9a-f]{40}\/tokens$/],
  ["GET", /^\/token\/[0-9a-f]{40}\/balance\/[0-9a-f]{40}$/],
  ["GET", /^\/token\/[0-9a-f]{40}\/history\/[0-9a-f]{40}$/],
  ["GET", /^\/(?:balance|history)\/[0-9a-f]{40}$/],
  ["GET", /^\/transactions\/recent$/],
  ["GET", /^\/network\/history$/],
  ["GET", /^\/network\/mint_history$/],
  ["GET", /^\/block\/\d+$/],
  ["GET", /^\/transaction\/[0-9a-f]{64}$/],
  ["GET", /^\/transaction\/envelope\/[0-9a-f]{40}$/],
  ["GET", /^\/nodes\/audit\/cached$/],
  ["GET", /^\/pools$/],
  ["POST", /^\/transaction$/],
  ["POST", /^\/transaction\/[0-9a-f]{64}\/cancel$/],
  ["POST", /^\/pools\/register$/],
  ["POST", /^\/nodes\/submit$/],
];

const ADMIN_ROUTES = [
  ["GET", /^\/nodes\/(?:discover|audit)$/],
  ["POST", /^\/nodes\/(?:sync_now|register)$/],
];

function matches(routes, method, path) {
  return routes.some(([allowedMethod, pattern]) => (
    allowedMethod === method && pattern.test(path)
  ));
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

const DEFAULT_NODE_URL = "https://node.hlxchain.com";

function nodeBases(rawValue) {
  // Fall back to the public seed node so a freshly forked wallet works with no
  // configuration; set HELIX_NODE_URL to point at your own node instead.
  if (!rawValue) rawValue = DEFAULT_NODE_URL;
  let values = rawValue;
  if (typeof rawValue === "string") {
    const trimmed = rawValue.trim();
    if (trimmed.startsWith("[")) {
      try {
        values = JSON.parse(trimmed);
      } catch (_) {
        throw new Error("HELIX_NODE_URL contains invalid JSON");
      }
    } else {
      values = [trimmed];
    }
  }
  if (!Array.isArray(values) || values.length === 0 || values.length > 10) {
    throw new Error("HELIX_NODE_URL must be one URL or a JSON array of 1 to 10 URLs");
  }
  const normalized = [];
  for (const value of values) {
    if (typeof value !== "string" || !value.trim()) {
      throw new Error("Every HELIX_NODE_URL entry must be a URL string");
    }
    const base = new URL(value.trim());
    const loopbackHttp = base.protocol === "http:" && [
      "localhost", "127.0.0.1", "[::1]",
    ].includes(base.hostname.toLowerCase());
    if (base.protocol !== "https:" && !loopbackHttp) {
      throw new Error("HELIX_NODE_URL entries must use HTTPS except for local development loopback URLs");
    }
    base.hash = "";
    base.search = "";
    base.username = "";
    base.password = "";
    const text = base.toString().replace(/\/$/, "");
    if (!normalized.includes(text)) normalized.push(text);
  }
  return normalized;
}

function upstreamUrl(rawBase, path, search) {
  const target = new URL(rawBase);
  target.pathname = `${target.pathname.replace(/\/$/, "")}${path}`;
  target.search = search;
  target.hash = "";
  target.username = "";
  target.password = "";
  return target;
}

const CANONICAL_HOST = "wallet.hlxchain.com";
// Alternate hostnames that should permanently redirect to the canonical wallet
// domain. Preview deployments (random-hash.helixwallet.pages.dev) are left alone
// so they stay testable.
const REDIRECT_HOSTS = new Set([
  "helixwallet.pages.dev",
  "hlxchain.com",
  "www.hlxchain.com",
]);

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);

    if (REDIRECT_HOSTS.has(incoming.hostname)) {
      const target = `https://${CANONICAL_HOST}${incoming.pathname}${incoming.search}`;
      return Response.redirect(target, 301);
    }

    if (!incoming.pathname.startsWith("/api/")) {
      // Payment-request link preview: for /?to=<addr>&amount=<n>, rewrite the
      // Open Graph / Twitter tags so iMessage and social unfurls show the amount.
      const to = (incoming.searchParams.get("to") || "").toLowerCase();
      if (incoming.pathname === "/" && /^[0-9a-f]{40}$/.test(to)) {
        const assetResponse = await env.ASSETS.fetch(request);
        if ((assetResponse.headers.get("content-type") || "").includes("text/html")) {
          const amount = incoming.searchParams.get("amount");
          const amountOk = amount && /^[0-9]+(\.[0-9]+)?$/.test(amount);
          const shortAddr = `${to.slice(0, 6)}…${to.slice(-4)}`;
          const title = "Helix payment request";
          const description = amountOk
            ? `Request for ${amount} HLX to ${shortAddr}`
            : `Send HLX to ${shortAddr}`;
          const setContent = value => ({ element(el) { el.setAttribute("content", value); } });
          return new HTMLRewriter()
            .on('meta[property="og:title"]', setContent(title))
            .on('meta[property="og:description"]', setContent(description))
            .on('meta[name="twitter:title"]', setContent(title))
            .on('meta[name="twitter:description"]', setContent(description))
            .transform(assetResponse);
        }
        return assetResponse;
      }
      return env.ASSETS.fetch(request);
    }

    const path = incoming.pathname.slice(4);
    const method = request.method.toUpperCase();
    const isPublic = matches(PUBLIC_ROUTES, method, path);
    const isAdmin = matches(ADMIN_ROUTES, method, path);
    if (!isPublic && !isAdmin) {
      return json({ message: "API route not available through the web gateway" }, 404);
    }
    if (isAdmin && env.HELIX_ENABLE_ADMIN_API !== "true") {
      return json({
        message: "Administrative web routes are disabled. Set HELIX_ENABLE_ADMIN_API=true in Cloudflare Pages to enable them.",
      }, 403);
    }

    const declaredLength = Number(request.headers.get("content-length") || 0);
    if (declaredLength > 1_048_576) {
      return json({ message: "Request body too large" }, 413);
    }

    let bases;
    let targets;
    try {
      bases = nodeBases(env.HELIX_NODE_URL);
      targets = bases.map(base => (
        upstreamUrl(base, path, incoming.search)
      ));
      if (targets.some(target => target.origin === incoming.origin)) {
        throw new Error("HELIX_NODE_URL entries must not point back to this Pages site");
      }
    } catch (error) {
      return json({ message: error.message }, 503);
    }

    let body;
    if (method !== "GET" && method !== "HEAD") {
      body = await request.arrayBuffer();
      if (body.byteLength > 1_048_576) {
        return json({ message: "Request body too large" }, 413);
      }
    }

    const originalClientIp = request.headers.get("cf-connecting-ip");
    const headers = new Headers(request.headers);
    for (const name of [
      "host", "origin", "cookie", "authorization", "proxy-authorization",
      "referer", "cf-access-jwt-assertion", "cf-connecting-ip", "cf-ray", "cf-visitor",
      "x-forwarded-for", "x-forwarded-proto", "x-helix-api-key", "x-helix-client-ip",
    ]) {
      headers.delete(name);
    }
    headers.set("accept", "application/json");
    if (env.HELIX_ADMIN_API_KEY) {
      headers.set("x-helix-api-key", env.HELIX_ADMIN_API_KEY);
    }
    if (originalClientIp) {
      headers.set("x-helix-client-ip", originalClientIp);
    }

    // Choose one known-live node before an administrative operation. The
    // operation itself is never retried. This also avoids dead first entries
    // in a node URL array.
    let adminTarget = null;
    if (isAdmin) {
      for (let index = 0; index < bases.length; index += 1) {
        try {
          const probe = await fetch(upstreamUrl(bases[index], "/health", ""), {
            method: "GET",
            headers,
            redirect: "manual",
          });
          const healthy = probe.ok;
          try { await probe.body?.cancel(); } catch (_) {}
          if (healthy) {
            adminTarget = targets[index];
            break;
          }
        } catch (_) {}
      }
      if (!adminTarget) {
        return json({ message: "No configured Helix node passed the health check" }, 502);
      }
    }

    const canFailOver = method === "GET" || method === "HEAD" || (
      method === "POST" && (
        path === "/transaction" || /^\/transaction\/[0-9a-f]{64}\/cancel$/.test(path)
      )
    );
    const attempts = isAdmin ? [adminTarget] : canFailOver ? targets : targets.slice(0, 1);
    for (let index = 0; index < attempts.length; index += 1) {
      try {
        const upstream = await fetch(attempts[index], {
          method,
          headers,
          body,
          redirect: "manual",
        });
        const hasFallback = index + 1 < attempts.length;
        if (hasFallback && upstream.status >= 500) {
          try { await upstream.body?.cancel(); } catch (_) {}
          continue;
        }
        const responseHeaders = new Headers();
        responseHeaders.set(
          "content-type",
          upstream.headers.get("content-type") || "application/json; charset=utf-8",
        );
        responseHeaders.set("cache-control", "no-store");
        return new Response(upstream.body, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers: responseHeaders,
        });
      } catch (_) {
        if (index + 1 >= attempts.length) break;
      }
    }
    return json({ message: "All configured Helix nodes are unreachable from Cloudflare" }, 502);
  },
};
