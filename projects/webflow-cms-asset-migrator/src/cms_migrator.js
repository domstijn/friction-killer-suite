/**
 * Webflow CMS CSV parser, Webflow CDN extractor, deterministic slug renamer,
 * Rich-Text HTML <img> rewriter, and 301-redirects.csv generator.
 */

export const FREE_ITEM_CAP = 15;

export const WEBFLOW_CDN_REGEX =
  /https?:\/\/(?:uploads-ssl\.webflow\.com|cdn\.prod\.website-files\.com|assets(?:-global)?\.website-files\.com)\/[^\s"'<>,)]+/gi;

const KNOWN_EXT_REGEX = /\.(webp|png|jpe?g|svg|avif|gif|pdf|mp4|webm|woff2?|json)$/i;

export function slugifyField(input, fallback = "item") {
  const clean = String(input || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return clean || fallback;
}

export function parseCsv(text) {
  const rows = [];
  const src = String(text || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  if (!src.trim()) return rows;

  let row = [];
  let cell = "";
  let inQuotes = false;

  for (let i = 0; i < src.length; i++) {
    const ch = src[i];
    if (inQuotes) {
      if (ch === '"') {
        if (src[i + 1] === '"') {
          cell += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        cell += ch;
      }
      continue;
    }

    if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(cell);
      cell = "";
    } else if (ch === "\n") {
      row.push(cell);
      if (row.some((c) => c !== "")) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += ch;
    }
  }

  if (cell !== "" || row.length > 0) {
    row.push(cell);
    if (row.some((c) => c !== "")) rows.push(row);
  }
  return rows;
}

export function serializeCsv(rows) {
  return rows
    .map((r) =>
      r
        .map((cell) => {
          const val = String(cell ?? "");
          if (/[",\n\r]/.test(val)) {
            return `"${val.replace(/"/g, '""')}"`;
          }
          return val;
        })
        .join(",")
    )
    .join("\n");
}

export function extractInlineUrls(text) {
  const matches = String(text || "").match(WEBFLOW_CDN_REGEX) || [];
  return Array.from(new Set(matches));
}

function getExtensionFromUrl(urlStr) {
  try {
    const pathname = new URL(urlStr).pathname;
    const match = pathname.match(KNOWN_EXT_REGEX);
    if (match) return `.${match[1].toLowerCase()}`;
  } catch {
    const match = String(urlStr || "").split("?")[0].match(KNOWN_EXT_REGEX);
    if (match) return `.${match[1].toLowerCase()}`;
  }
  return ".png";
}

function isRichTextCell(cellVal, headerName) {
  const trimmed = String(cellVal || "").trim();
  if (!trimmed) return false;
  if (/<[a-z][\s\S]*>/i.test(trimmed)) return true;
  if (/^(?:https?:\/\/\S+(?:\s*[;\n]\s*https?:\/\/\S+)*)$/i.test(trimmed)) return false;
  return /body|content|rich|html|details|summary|description/i.test(String(headerName || ""));
}

export function migrateWebflowCmsCsv(csvText, options = {}) {
  const {
    isPro = false,
    targetBaseUrl = "/assets/cms",
    oldPathPrefix = "/blog",
    newPathPrefix = "/posts",
    rewriteRichText = false,
    generateRedirects = false,
  } = options;

  if (!isPro && (rewriteRichText || generateRedirects)) {
    return {
      ok: false,
      blockedByTier: true,
      reason:
        "Inline Rich-Text HTML CDN rewriting and 301 redirect pack generation require a Pro license key.",
    };
  }

  const rows = parseCsv(csvText);
  if (rows.length < 2) {
    return {
      ok: false,
      error: "CSV must contain a header row and at least one CMS item row.",
    };
  }

  const headers = rows[0];
  const dataRows = rows.slice(1);
  const totalItems = dataRows.length;
  const maxRows = isPro ? totalItems : Math.min(totalItems, FREE_ITEM_CAP);
  const truncatedItems = Math.max(0, totalItems - maxRows);

  let slugIdx = headers.findIndex((h) => /^slug$/i.test(h.trim()));
  if (slugIdx < 0) slugIdx = headers.findIndex((h) => /slug/i.test(h));
  if (slugIdx < 0) slugIdx = headers.findIndex((h) => /^name$|^title$/i.test(h.trim()));

  const cleanBase = String(targetBaseUrl || "/assets/cms").replace(/\/+$/, "");
  const oldClean = "/" + String(oldPathPrefix || "blog").replace(/^\/+|\/+$/g, "");
  const newClean = "/" + String(newPathPrefix || "posts").replace(/^\/+|\/+$/g, "");

  const urlMap = new Map();
  const counters = new Map();
  const assetManifest = [];
  let skippedRichTextUrls = 0;

  function registerAsset(originalUrl, itemSlug, fieldHeader, source) {
    if (urlMap.has(originalUrl)) {
      return urlMap.get(originalUrl);
    }
    const fieldSlug = slugifyField(fieldHeader, "media");
    const counterKey = `${itemSlug}::${fieldSlug}`;
    const idx = (counters.get(counterKey) || 0) + 1;
    counters.set(counterKey, idx);
    const ext = getExtensionFromUrl(originalUrl);
    const fileName = `${itemSlug}-${fieldSlug}-${String(idx).padStart(2, "0")}${ext}`;
    const newUrl = `${cleanBase}/${fileName}`;
    const entry = {
      originalUrl,
      fileName,
      newUrl,
      slug: itemSlug,
      field: fieldHeader,
      source,
    };
    urlMap.set(originalUrl, entry);
    assetManifest.push(entry);
    return entry;
  }

  const rewrittenRows = [];
  const redirectRows = [];

  for (let r = 0; r < maxRows; r++) {
    const srcRow = dataRows[r];
    const itemSlug = slugifyField(
      slugIdx >= 0 ? srcRow[slugIdx] : "",
      `item-${r + 1}`
    );

    const nextRow = headers.map((headerName, c) => {
      const cell = srcRow[c] ?? "";
      const urls = extractInlineUrls(cell);
      if (urls.length === 0) return cell;

      const rich = isRichTextCell(cell, headerName);
      if (rich && !rewriteRichText) {
        skippedRichTextUrls += urls.length;
        return cell;
      }

      return cell.replace(WEBFLOW_CDN_REGEX, (matchedUrl) => {
        const mapped = registerAsset(
          matchedUrl,
          itemSlug,
          headerName || `col-${c + 1}`,
          rich ? "rich_text_html" : "media_column"
        );
        return mapped.newUrl;
      });
    });

    rewrittenRows.push(nextRow);

    if (isPro && generateRedirects && slugIdx >= 0 && String(srcRow[slugIdx] || "").trim()) {
      redirectRows.push([`${oldClean}/${itemSlug}`, `${newClean}/${itemSlug}`, "301"]);
    }
  }

  return {
    ok: true,
    isPro,
    totalItems,
    processedItems: maxRows,
    truncatedItems,
    assetsFound: assetManifest.length,
    skippedRichTextUrls,
    assetManifest,
    rewrittenCsv: serializeCsv([headers, ...rewrittenRows]),
    redirectsCsv:
      isPro && generateRedirects
        ? serializeCsv([["old_path", "new_path", "status"], ...redirectRows])
        : null,
  };
}
