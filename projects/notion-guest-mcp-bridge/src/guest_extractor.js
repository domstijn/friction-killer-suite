/**
 * Deterministic Notion Guest page -> AI/MCP Context Pack engine.
 * Zero external dependencies; runs in Chrome MV3 service worker and Node ESM tests.
 */

export const FREE_DAILY_CAP = 3;
export const FREE_BLOCK_CAP = 40;

const EMAIL_RE = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
const SECRET_RE = /\b(?:sk_(?:live|test)|pk_(?:live|test)|lin_api|ntn_|secret_|ghp_|xoxb-)[A-Za-z0-9_-]{8,}\b/g;
const BEARER_RE = /\bBearer\s+[A-Za-z0-9._-]{10,}\b/gi;

export function redactClientPii(text) {
  let out = String(text || "");
  out = out.replace(EMAIL_RE, "[EMAIL_REDACTED]");
  out = out.replace(SECRET_RE, "[SECRET_REDACTED]");
  out = out.replace(BEARER_RE, "Bearer [TOKEN_REDACTED]");
  return out;
}

function scrubPage(page) {
  return {
    ...page,
    title: redactClientPii(page.title),
    blocks: (page.blocks || []).map((b) => ({ ...b, text: redactClientPii(b.text || "") })),
    tables: (page.tables || []).map((t) => ({
      title: redactClientPii(t.title || "Table"),
      headers: (t.headers || []).map((h) => redactClientPii(h)),
      rows: (t.rows || []).map((row) => row.map((cell) => redactClientPii(cell))),
    })),
  };
}

function renderTableMarkdown(table) {
  const headers = table.headers || [];
  if (headers.length === 0) return "";
  const lines = [
    `### ${table.title || "Inline Table"}`,
    `| ${headers.join(" | ")} |`,
    `| ${headers.map(() => "---").join(" | ")} |`,
  ];
  for (const row of table.rows || []) {
    const padded = headers.map((_, i) => String(row[i] ?? "").replace(/\|/g, "\\|"));
    lines.push(`| ${padded.join(" | ")} |`);
  }
  return lines.join("\n");
}

export function formatGuestPageMarkdown(page, { blockLimit = null } = {}) {
  const title = String(page?.title || "Untitled Client Page").trim();
  const url = String(page?.url || "").trim();
  const blocks = Array.isArray(page?.blocks) ? page.blocks : [];
  const usedBlocks = blockLimit != null ? blocks.slice(0, blockLimit) : blocks;
  const truncatedBlocks = Math.max(0, blocks.length - usedBlocks.length);

  const lines = [`# ${title}`];
  if (url) lines.push(`> Source: ${url}`);
  lines.push("");

  for (const b of usedBlocks) {
    const text = String(b?.text || "").trim();
    if (!text) continue;
    if (b.type === "heading") {
      const level = Math.min(4, Math.max(2, Number(b.level || 2)));
      lines.push(`${"#".repeat(level)} ${text}`);
    } else if (b.type === "todo") {
      lines.push(`- [${b.checked ? "x" : " "}] ${text}`);
    } else if (b.type === "callout") {
      lines.push(`> [Note] ${text}`);
    } else if (b.type === "code") {
      lines.push("```" + (b.lang || ""));
      lines.push(text);
      lines.push("```");
    } else {
      lines.push(text);
    }
  }

  for (const tbl of page?.tables || []) {
    const md = renderTableMarkdown(tbl);
    if (md) {
      lines.push("");
      lines.push(md);
    }
  }

  return {
    markdown: lines.join("\n").trim(),
    totalBlocks: blocks.length,
    includedBlocks: usedBlocks.length,
    truncatedBlocks,
    tableCount: Array.isArray(page?.tables) ? page.tables.length : 0,
  };
}

export function buildGuestContextPack(
  rawPages,
  {
    isPro = false,
    dailyUsed = 0,
    freeDailyCap = FREE_DAILY_CAP,
    freeBlockCap = FREE_BLOCK_CAP,
    redactPii = false,
  } = {}
) {
  const pages = (Array.isArray(rawPages) ? rawPages : [rawPages]).filter(Boolean);
  if (pages.length === 0) {
    return {
      ok: false,
      blockedByTier: false,
      reason: "No Notion page blocks extracted. Open a Notion page you have guest access to.",
    };
  }

  if (!isPro && pages.length > 1) {
    return {
      ok: false,
      blockedByTier: true,
      reason: "Multi-page guest queueing & bundled export requires an active Pro license key.",
    };
  }

  if (!isPro && redactPii) {
    return {
      ok: false,
      blockedByTier: true,
      reason: "Automatic client email/API token redaction requires an active Pro license key.",
    };
  }

  if (!isPro && dailyUsed >= freeDailyCap) {
    return {
      ok: false,
      blockedByTier: true,
      reason: `Free tier limit reached (${dailyUsed}/${freeDailyCap} packs/day). Upgrade to Pro for unlimited guest packs, PII redaction, and .mcp-context.json export.`,
    };
  }

  const processed = pages.map((raw) => {
    const clean = isPro && redactPii ? scrubPage(raw) : raw;
    const formatted = formatGuestPageMarkdown(clean, {
      blockLimit: isPro ? null : freeBlockCap,
    });
    return {
      title: clean.title || "Untitled Client Page",
      url: clean.url || "",
      ...formatted,
      tables: isPro ? clean.tables || [] : [],
    };
  });

  const combinedMarkdown = processed.map((p) => p.markdown).join("\n\n---\n\n");
  const result = {
    ok: true,
    blockedByTier: false,
    isPro,
    pageCount: processed.length,
    redactedPii: Boolean(isPro && redactPii),
    markdown: combinedMarkdown,
    truncatedBlocks: processed.reduce((acc, p) => acc + p.truncatedBlocks, 0),
    tablesIncluded: isPro ? processed.reduce((acc, p) => acc + p.tableCount, 0) : 0,
  };

  if (isPro) {
    result.mcpContextJson = JSON.stringify(
      {
        schema: "mcp.guest.context/v1",
        source: "NotionGuestBridge",
        pageCount: processed.length,
        redactedPii: Boolean(redactPii),
        pages: processed.map((p) => ({
          title: p.title,
          url: p.url,
          blocksIncluded: p.includedBlocks,
          tables: p.tables,
        })),
        markdown: combinedMarkdown,
      },
      null,
      2
    );
  } else {
    result.mcpContextJson = null;
  }

  return result;
}
