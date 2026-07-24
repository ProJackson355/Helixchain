var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// _worker.js
var PUBLIC_ROUTES = [
  ["GET", /^\/(?:chain|pending|nodes|stats|health)$/],
  ["GET", /^\/tokens$/],
  ["GET", /^\/token\/[0-9a-f]{40}$/],
  ["GET", /^\/token\/[0-9a-f]{40}\/market\/history$/],
  ["GET", /^\/dad\/[0-9a-f]{40}\/tokens$/],
  ["GET", /^\/token\/[0-9a-f]{40}\/balance\/[0-9a-f]{40}$/],
  ["GET", /^\/token\/[0-9a-f]{40}\/history\/[0-9a-f]{40}$/],
  ["GET", /^\/(?:balance|history)\/[0-9a-f]{40}$/],
  ["GET", /^\/transactions\/recent$/],
  ["GET", /^\/transaction\/[0-9a-f]{64}$/],
  ["GET", /^\/nodes\/audit\/cached$/],
  ["POST", /^\/transaction$/],
  ["POST", /^\/transaction\/[0-9a-f]{64}\/cancel$/]
];
var ADMIN_ROUTES = [
  ["GET", /^\/nodes\/(?:discover|audit)$/],
  ["GET", /^\/mine\/status\/[0-9a-f]{32}$/],
  ["POST", /^\/(?:mine|mine\/start|nodes\/sync_now|nodes\/register)$/]
];
function matches(routes, method, path) {
  return routes.some(([allowedMethod, pattern]) => allowedMethod === method && pattern.test(path));
}
__name(matches, "matches");
function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store"
    }
  });
}
__name(json, "json");
function nodeBases(rawValue) {
  if (!rawValue) throw new Error("HELIX_NODE_URL is not configured");
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
    if (!/^https?:$/.test(base.protocol)) {
      throw new Error("HELIX_NODE_URL entries must use http or https");
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
__name(nodeBases, "nodeBases");
function upstreamUrl(rawBase, path, search) {
  const target = new URL(rawBase);
  target.pathname = `${target.pathname.replace(/\/$/, "")}${path}`;
  target.search = search;
  target.hash = "";
  target.username = "";
  target.password = "";
  return target;
}
__name(upstreamUrl, "upstreamUrl");
var worker_default = {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    if (!incoming.pathname.startsWith("/api/")) {
      return env.ASSETS.fetch(request);
    }
    const path = incoming.pathname.slice(4);
    const method = request.method.toUpperCase();
    const isPublic = matches(PUBLIC_ROUTES, method, path);
    const isAdmin = matches(ADMIN_ROUTES, method, path);
    if (!isPublic && !isAdmin) {
      return json({ message: "API route not available through the web_old gateway" }, 404);
    }
    if (isAdmin && env.HELIX_ENABLE_ADMIN_API !== "true") {
      return json({
        message: "Administrative web_old routes are disabled. Set HELIX_ENABLE_ADMIN_API=true in Cloudflare Pages to enable them."
      }, 403);
    }
    const declaredLength = Number(request.headers.get("content-length") || 0);
    if (declaredLength > 1048576) {
      return json({ message: "Request body too large" }, 413);
    }
    let bases;
    let targets;
    try {
      bases = nodeBases(env.HELIX_NODE_URL);
      targets = bases.map((base) => upstreamUrl(base, path, incoming.search));
      if (targets.some((target) => target.origin === incoming.origin)) {
        throw new Error("HELIX_NODE_URL entries must not point back to this Pages site");
      }
    } catch (error) {
      return json({ message: error.message }, 503);
    }
    let body;
    if (method !== "GET" && method !== "HEAD") {
      body = await request.arrayBuffer();
      if (body.byteLength > 1048576) {
        return json({ message: "Request body too large" }, 413);
      }
    }
    const originalClientIp = request.headers.get("cf-connecting-ip");
    const headers = new Headers(request.headers);
    for (const name of [
      "host",
      "origin",
      "cf-connecting-ip",
      "cf-ray",
      "cf-visitor",
      "x-forwarded-for",
      "x-forwarded-proto",
      "x-helix-api-key",
      "x-helix-client-ip"
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
    let adminTarget = null;
    if (isAdmin) {
      for (let index = 0; index < bases.length; index += 1) {
        try {
          const probe = await fetch(upstreamUrl(bases[index], "/health", ""), {
            method: "GET",
            headers,
            redirect: "manual"
          });
          const healthy = probe.ok;
          try {
            await probe.body?.cancel();
          } catch (_) {
          }
          if (healthy) {
            adminTarget = targets[index];
            break;
          }
        } catch (_) {
        }
      }
      if (!adminTarget) {
        return json({ message: "No configured Helix node passed the health check" }, 502);
      }
    }
    const canFailOver = method === "GET" || method === "HEAD" || method === "POST" && (path === "/transaction" || /^\/transaction\/[0-9a-f]{64}\/cancel$/.test(path));
    const attempts = isAdmin ? [adminTarget] : canFailOver ? targets : targets.slice(0, 1);
    for (let index = 0; index < attempts.length; index += 1) {
      try {
        const upstream = await fetch(attempts[index], {
          method,
          headers,
          body,
          redirect: "manual"
        });
        const hasFallback = index + 1 < attempts.length;
        if (hasFallback && upstream.status >= 500) {
          try {
            await upstream.body?.cancel();
          } catch (_) {
          }
          continue;
        }
        const responseHeaders = new Headers();
        responseHeaders.set(
          "content-type",
          upstream.headers.get("content-type") || "application/json; charset=utf-8"
        );
        responseHeaders.set("cache-control", "no-store");
        return new Response(upstream.body, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers: responseHeaders
        });
      } catch (_) {
        if (index + 1 >= attempts.length) break;
      }
    }
    return json({ message: "All configured Helix nodes are unreachable from Cloudflare" }, 502);
  }
};
export {
  worker_default as default
};
//# sourceMappingURL=bundledWorker-0.9189231159352089.mjs.map
