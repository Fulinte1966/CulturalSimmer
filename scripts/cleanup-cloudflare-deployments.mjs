/** Delete inactive Pages deployments after a clean production replacement. */

const token = process.env.CLOUDFLARE_API_TOKEN;
const accountId = process.env.CLOUDFLARE_ACCOUNT_ID;
const projectName = process.env.CLOUDFLARE_PAGES_PROJECT ?? "fulinte";
const retainedBranches = new Set(
  (
    process.env.CLOUDFLARE_KEEP_BRANCHES ??
    "main,ebook-preview,removal-preview,catalog-reset-preview"
  )
    .split(",")
    .map((branch) => branch.trim())
    .filter(Boolean),
);

if (!token || !accountId) {
  throw new Error(
    "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID are required",
  );
}

const apiRoot = `https://api.cloudflare.com/client/v4/accounts/${accountId}/pages/projects/${projectName}`;

async function cloudflare(pathname, init = {}) {
  const response = await fetch(`${apiRoot}${pathname}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  const payload =
    response.status === 204 ? { success: true } : await response.json();
  if (!response.ok || payload.success === false) {
    throw new Error(
      `Cloudflare Pages API failed (${response.status}): ${JSON.stringify(payload.errors ?? payload)}`,
    );
  }
  return payload;
}

const deployments = [];
for (let page = 1; ; page += 1) {
  // Pages rejects unsupported page sizes. Let the API choose its documented
  // default and follow the returned pagination metadata instead.
  const payload = await cloudflare(`/deployments?page=${page}`);
  deployments.push(...payload.result);
  if (page >= Number(payload.result_info?.total_pages ?? 1)) break;
}

const newestByBranch = new Map();
for (const deployment of deployments) {
  const branch = deployment.deployment_trigger?.metadata?.branch ?? "";
  if (!retainedBranches.has(branch) || newestByBranch.has(branch)) continue;
  newestByBranch.set(branch, deployment.id);
}

const protectedIds = new Set(newestByBranch.values());
const stale = deployments.filter(
  (deployment) => !protectedIds.has(deployment.id),
);
for (const deployment of stale) {
  await cloudflare(`/deployments/${deployment.id}?force=true`, {
    method: "DELETE",
  });
}

console.log(
  `Deleted ${stale.length} inactive deployment(s); retained the latest deployment for ${protectedIds.size} branch(es).`,
);
