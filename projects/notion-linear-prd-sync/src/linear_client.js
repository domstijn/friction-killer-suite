/**
 * Zero-dependency Linear GraphQL client for creating PRD Epics, Sub-Issues, and reading statuses.
 */

const LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql";

const ISSUE_CREATE_MUTATION = `
  mutation IssueCreate($input: IssueCreateInput!) {
    issueCreate(input: $input) {
      success
      issue {
        id
        identifier
        title
        url
      }
    }
  }
`;

const ISSUE_BY_KEY_QUERY = `
  query IssuesByFilter($filter: IssueFilter) {
    issues(filter: $filter, first: 50) {
      nodes {
        identifier
        state {
          name
        }
      }
    }
  }
`;

async function graphqlRequest({ apiKey, query, variables, fetchImpl = globalThis.fetch }) {
  if (!apiKey || !String(apiKey).trim()) {
    throw new Error("Linear API key is required");
  }
  const res = await fetchImpl(LINEAR_GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: String(apiKey).trim(),
    },
    body: JSON.stringify({ query, variables }),
  });

  const payload = await res.json().catch(() => ({}));
  if (!res.ok || payload?.errors?.length) {
    const msg = payload?.errors?.[0]?.message || `Linear API HTTP ${res.status}`;
    throw new Error(msg);
  }
  return payload.data;
}

/**
 * Create Linear parent epic (when Pro tier enabled) and child/flat issues from a parsed PRD.
 */
export async function pushPrdToLinear({
  apiKey,
  teamId,
  parsedPrd,
  tierPlan,
  priority = 0,
  fetchImpl = globalThis.fetch,
}) {
  if (!teamId || !String(teamId).trim()) {
    throw new Error("Linear Team ID is required");
  }
  const tasks = tierPlan?.tasksToCreate || [];
  if (tasks.length === 0) {
    return { createdParent: null, createdIssues: [] };
  }

  let createdParent = null;
  if (tierPlan.createParentEpic) {
    const parentInput = {
      teamId: String(teamId).trim(),
      title: `[PRD] ${parsedPrd.title}`,
      description: parsedPrd.summary,
      ...(priority > 0 ? { priority } : {}),
    };
    const data = await graphqlRequest({
      apiKey,
      query: ISSUE_CREATE_MUTATION,
      variables: { input: parentInput },
      fetchImpl,
    });
    if (!data?.issueCreate?.success || !data?.issueCreate?.issue) {
      throw new Error("Failed to create parent PRD issue in Linear");
    }
    createdParent = data.issueCreate.issue;
  }

  const createdIssues = [];
  for (const task of tasks) {
    const input = {
      teamId: String(teamId).trim(),
      title: task.title,
      description: task.description,
      ...(createdParent?.id ? { parentId: createdParent.id } : {}),
      ...(priority > 0 ? { priority } : {}),
    };
    const data = await graphqlRequest({
      apiKey,
      query: ISSUE_CREATE_MUTATION,
      variables: { input },
      fetchImpl,
    });
    if (!data?.issueCreate?.success || !data?.issueCreate?.issue) {
      throw new Error(`Failed to create Linear issue for "${task.title}"`);
    }
    createdIssues.push(data.issueCreate.issue);
  }

  return { createdParent, createdIssues };
}

/**
 * Fetch live Linear workflow state names for a list of issue identifiers (e.g. ["ENG-101"]).
 */
export async function fetchLinearStatuses({ apiKey, issueKeys = [], fetchImpl = globalThis.fetch }) {
  const unique = [...new Set(issueKeys)].filter((k) => /^[A-Z][A-Z0-9]+-\d+$/.test(k));
  if (unique.length === 0) return {};

  const orFilters = unique.map((key) => {
    const [teamKey, numStr] = key.split("-");
    return {
      team: { key: { eq: teamKey } },
      number: { eq: Number(numStr) },
    };
  });

  const data = await graphqlRequest({
    apiKey,
    query: ISSUE_BY_KEY_QUERY,
    variables: { filter: { or: orFilters } },
    fetchImpl,
  });

  const statusMap = {};
  for (const node of data?.issues?.nodes || []) {
    if (node?.identifier && node?.state?.name) {
      statusMap[node.identifier] = node.state.name;
    }
  }
  return statusMap;
}
