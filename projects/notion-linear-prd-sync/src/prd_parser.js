/**
 * Pure-JS Notion PRD parser, Free/Pro tier enforcer, and status badge formatter.
 */

const HEADING_RE = /^(#{1,3})\s+(.+)$/;
const CHECKLIST_RE = /^(?:[-*]\s*)?\[([ xX]?)\]\s+(.+)$/;
const UNICODE_TODO_RE = /^([☐☑✓])\s+(.+)$/;
const ISSUE_KEY_RE = /\[([A-Z][A-Z0-9]+-\d+)(?::\s*[^\]]+)?\]/;

/**
 * Parse Notion/Markdown PRD text into headings, summary, and structured checklist tasks.
 */
export function parseNotionPrd(rawText, { pageTitle = "Untitled PRD" } = {}) {
  const lines = String(rawText || "").split(/\r?\n/);
  let resolvedTitle = pageTitle;
  let currentSection = "General";
  const sections = [];
  const summaryLines = [];
  const tasks = [];

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;

    const hMatch = line.match(HEADING_RE);
    if (hMatch) {
      const level = hMatch[1].length;
      const headingText = hMatch[2].trim();
      if (level === 1 && resolvedTitle === "Untitled PRD") {
        resolvedTitle = headingText;
      } else {
        currentSection = headingText;
        if (!sections.includes(headingText)) sections.push(headingText);
      }
      continue;
    }

    let completed = null;
    let body = "";
    const cMatch = line.match(CHECKLIST_RE);
    if (cMatch) {
      completed = cMatch[1].toLowerCase() === "x";
      body = cMatch[2].trim();
    } else {
      const uMatch = line.match(UNICODE_TODO_RE);
      if (uMatch) {
        completed = uMatch[1] !== "☐";
        body = uMatch[2].trim();
      }
    }

    if (completed !== null) {
      const keyMatch = body.match(ISSUE_KEY_RE);
      const existingIssueKey = keyMatch ? keyMatch[1] : null;
      const cleanTitle = body.replace(ISSUE_KEY_RE, "").trim();
      if (cleanTitle) {
        tasks.push({
          title: cleanTitle,
          section: currentSection,
          completed,
          description: `**Section:** ${currentSection}\n\n${cleanTitle}`,
          existingIssueKey,
        });
      }
      continue;
    }

    if (summaryLines.length < 4) {
      summaryLines.push(line);
    }
  }

  return {
    title: resolvedTitle,
    summary: summaryLines.join("\n") || `Imported from Notion PRD: ${resolvedTitle}`,
    sections,
    tasks,
  };
}

/**
 * Enforce Free vs. Pro tier rules on parsed PRD tasks.
 * - Skips completed items and tasks already tagged with an existing Linear issue key.
 * - Free tier caps pushes at `freeWeeklyCap` flat issues/week without Parent Epic nesting.
 * - Pro tier unlocks unlimited tasks + Parent Epic -> Sub-Issue hierarchy.
 */
export function enforceTierLimits(
  parsedPrd,
  { isPro = false, weeklyUsed = 0, freeWeeklyCap = 5 } = {}
) {
  const allTasks = parsedPrd?.tasks || [];
  const skippedSyncedCount = allTasks.filter((t) => Boolean(t.existingIssueKey)).length;
  const pendingTasks = allTasks.filter((t) => !t.existingIssueKey && !t.completed);

  if (pendingTasks.length === 0) {
    return {
      allowed: true,
      isPro: Boolean(isPro),
      createParentEpic: Boolean(isPro),
      tasksToCreate: [],
      skippedSyncedCount,
      truncatedCount: 0,
      remainingQuota: isPro ? Infinity : Math.max(0, freeWeeklyCap - weeklyUsed),
      reason: skippedSyncedCount > 0 ? "All open tasks are already synced" : "No open checklist tasks found",
    };
  }

  if (isPro) {
    return {
      allowed: true,
      isPro: true,
      createParentEpic: true,
      tasksToCreate: pendingTasks,
      skippedSyncedCount,
      truncatedCount: 0,
      remainingQuota: Infinity,
      reason: "Pro license active",
    };
  }

  const remaining = Math.max(0, freeWeeklyCap - weeklyUsed);
  if (remaining === 0) {
    return {
      allowed: false,
      isPro: false,
      createParentEpic: false,
      tasksToCreate: [],
      skippedSyncedCount,
      truncatedCount: pendingTasks.length,
      remainingQuota: 0,
      reason: `Free weekly cap (${freeWeeklyCap} issues) reached. Activate a Pro license key for unlimited PRD epics & sub-issues.`,
    };
  }

  const tasksToCreate = pendingTasks.slice(0, remaining).map((t) => ({
    ...t,
    description: t.title, // Free tier creates flat issues without rich section nesting
  }));

  return {
    allowed: true,
    isPro: false,
    createParentEpic: false,
    tasksToCreate,
    skippedSyncedCount,
    truncatedCount: Math.max(0, pendingTasks.length - tasksToCreate.length),
    remainingQuota: remaining - tasksToCreate.length,
    reason:
      pendingTasks.length > remaining
        ? `Free tier limited this push to ${remaining} issue(s); upgrade to Pro for full PRD batch & sub-issues.`
        : "Free tier quota available",
  };
}

/**
 * Extract unique Linear issue keys (e.g. ENG-101) referenced in raw PRD text.
 */
export function extractIssueKeys(rawText) {
  const matches = String(rawText || "").matchAll(new RegExp(ISSUE_KEY_RE.source, "g"));
  const keys = new Set();
  for (const m of matches) {
    keys.add(m[1]);
  }
  return [...keys];
}

/**
 * Update inline `[KEY]` or `[KEY: OldStatus]` badges with live Linear statuses.
 */
export function formatStatusBadges(rawText, statusByKey = {}) {
  return String(rawText || "")
    .split(/\r?\n/)
    .map((line) =>
      line.replace(new RegExp(ISSUE_KEY_RE.source, "g"), (full, key) => {
        const status = statusByKey[key];
        return status ? `[${key}: ${status}]` : full;
      })
    )
    .join("\n");
}
