const ALLOWED_ORIGIN = "https://domstijn.github.io";
const ALLOWED_EVENTS = new Set([
  "page_view",
  "tool_run",
  "file_upload",
  "paywall_hit",
  "checkout_click",
  "feedback_click",
]);
const BOT_UA_RE = /bot|crawl|spider|headless|curl|wget|python|slurp|bingpreview|lighthouse|facebookexternalhit/i;
const SLUG_RE = /^[a-z0-9_-]{1,64}$/;

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin === ALLOWED_ORIGIN ? ALLOWED_ORIGIN : ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

function jsonResponse(payload, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...extraHeaders,
    },
  });
}

function sanitizeRefHost(raw) {
  const cleaned = String(raw || "").trim().toLowerCase().replace(/^https?:\/\//, "").split("/")[0].split(":")[0];
  const safe = cleaned.replace(/[^a-z0-9.-]/g, "").slice(0, 64);
  return safe || "direct";
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      if (origin && origin !== ALLOWED_ORIGIN) {
        return new Response(null, { status: 403 });
      }
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    if (request.method === "GET" && url.pathname === "/health") {
      return jsonResponse({ ok: true, service: "fk-funnel-beacon", eu_d1: Boolean(env.DB) });
    }

    if (request.method === "GET" && url.pathname === "/stats") {
      const daysParam = parseInt(url.searchParams.get("days") || "30", 10);
      const days = Number.isFinite(daysParam) ? Math.min(Math.max(daysParam, 1), 90) : 30;
      const includeSelftest = url.searchParams.get("include_selftest") === "1";
      const modifier = "-" + days + " days";

      const sql = includeSelftest
        ? "SELECT day, slug, event, ref_host, cnt FROM daily_events WHERE day >= date('now', ?) ORDER BY day DESC, cnt DESC"
        : "SELECT day, slug, event, ref_host, cnt FROM daily_events WHERE day >= date('now', ?) AND slug != '_selftest' ORDER BY day DESC, cnt DESC";

      const res = await env.DB.prepare(sql).bind(modifier).all();
      const rows = res?.results || [];

      const totals_by_event = {};
      const totals_by_slug = {};
      const totals_by_referrer = {};

      for (const r of rows) {
        const c = Number(r.cnt || 0);
        totals_by_event[r.event] = (totals_by_event[r.event] || 0) + c;
        if (!totals_by_slug[r.slug]) totals_by_slug[r.slug] = {};
        totals_by_slug[r.slug][r.event] = (totals_by_slug[r.slug][r.event] || 0) + c;
        totals_by_referrer[r.ref_host] = (totals_by_referrer[r.ref_host] || 0) + c;
      }

      return jsonResponse({
        ok: true,
        generated_at: new Date().toISOString(),
        days,
        totals_by_event,
        totals_by_slug,
        totals_by_referrer,
        daily: rows,
      });
    }

    if (request.method === "POST" && url.pathname === "/e") {
      if (origin && origin !== ALLOWED_ORIGIN) {
        return jsonResponse({ ok: false, error: "Forbidden origin" }, 403);
      }
      const headers = corsHeaders(origin);
      let body;
      try {
        body = await request.json();
      } catch {
        return jsonResponse({ ok: false, error: "Invalid JSON" }, 400, headers);
      }

      const slug = String(body?.slug || "").trim().toLowerCase();
      const event = String(body?.event || "").trim().toLowerCase();
      if (!SLUG_RE.test(slug) || !ALLOWED_EVENTS.has(event)) {
        return jsonResponse({ ok: false, error: "Invalid slug or event" }, 400, headers);
      }

      const ua = request.headers.get("User-Agent") || "";
      if (slug !== "_selftest" && (!ua || BOT_UA_RE.test(ua))) {
        return jsonResponse({ ok: true, ignored: "bot" }, 202, headers);
      }

      const ref_host = sanitizeRefHost(body?.ref_host);
      const day = new Date().toISOString().slice(0, 10);

      await env.DB.prepare(
        "INSERT INTO daily_events (day, slug, event, ref_host, cnt) VALUES (?1, ?2, ?3, ?4, 1) " +
          "ON CONFLICT(day, slug, event, ref_host) DO UPDATE SET cnt = cnt + 1"
      )
        .bind(day, slug, event, ref_host)
        .run();

      return jsonResponse({ ok: true, day, slug, event, ref_host }, 202, headers);
    }

    return jsonResponse({ ok: false, error: "Not found" }, 404);
  },
};
