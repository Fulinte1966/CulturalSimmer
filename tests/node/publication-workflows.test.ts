import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { parse as parseYaml } from "yaml";

const root = path.resolve(new URL("../..", import.meta.url).pathname);

function workflow(name: string) {
  const source = fs.readFileSync(
    path.join(root, ".github/workflows", name),
    "utf8",
  );
  return { source, value: parseYaml(source) };
}

test("candidate publication keeps preview and production approval boundaries", () => {
  const { source, value } = workflow("ebook-candidate.yml");
  assert.equal(value.jobs.preview.environment, "cloudflare-pages");
  assert.equal(value.jobs.approval.environment, "ebook-production");
  assert.deepEqual(value.jobs.promote.needs, "approval");
  assert.equal(value.jobs.promote.environment, "cloudflare-pages");
  assert.match(source, /candidate_lock\.py verify/);
  assert.match(source, /Roll back an uncommitted canonical Release/);
  assert.match(source, /cloudflare-clean-dist/);
  assert.equal(value.permissions.actions, "write");
  assert.match(source, /gh workflow run deploy\.yml/);
  assert.match(source, /notify_updates=true/);
  assert.equal(
    value.jobs.promote.env.CLOUDFLARE_API_TOKEN,
    "${{ secrets.CLOUDFLARE_API_TOKEN }}",
  );
  assert.equal(
    value.jobs.promote.env.CLOUDFLARE_ACCOUNT_ID,
    "${{ vars.CLOUDFLARE_ACCOUNT_ID }}",
  );
});

test("publication removal requires a registered ledger and records failures", () => {
  const { source, value } = workflow("remove-publication.yml");
  assert.equal(value.jobs.candidate.environment, "cloudflare-pages");
  assert.equal(value.jobs.approval.environment, "ebook-production");
  assert.deepEqual(value.jobs.promote.needs, "approval");
  assert.equal(value.jobs.promote.environment, "cloudflare-pages");
  assert.match(source, /Verify private ledger registration/g);
  assert.match(source, /phase:"failed"/);
  assert.match(source, /cleanup-cloudflare-deployments\.mjs/);
});

test("only an explicit ingest deployment dispatches notifications after both hosts", () => {
  const { source, value } = workflow("deploy.yml");
  assert.equal(value.on.workflow_dispatch.inputs.notify_updates.default, false);
  assert.match(value.jobs.notify.if, /workflow_dispatch/);
  assert.match(value.jobs.notify.if, /notify_updates/);
  assert.deepEqual(value.jobs.notify.needs, ["deploy-cloudflare", "deploy"]);
  assert.match(source, /notify\.yml/);
  assert.match(source, /notify-ntfy\.yml/);
});

test("non-scheduled deployments report real-time operations state without blocking publication", () => {
  const { source, value } = workflow("deploy.yml");
  assert.match(value.jobs["ops-start"].if, /event_name != 'schedule'/);
  assert.equal(value.jobs["ops-start"]["continue-on-error"], true);
  assert.deepEqual(value.jobs["ops-finish"].needs, [
    "build",
    "deploy-cloudflare",
    "deploy",
  ]);
  assert.match(value.jobs["ops-finish"].if, /always\(\)/);
  assert.match(value.jobs["ops-finish"].if, /event_name != 'schedule'/);
  assert.equal(value.jobs["ops-finish"]["continue-on-error"], true);
  assert.match(source, /notify-ops\.yml/);
  assert.match(source, /site\.deploy/);
  assert.match(source, /"variant":"started"/);
  assert.match(source, /"variant":"failed"/);
});

test("pre-launch reset requires backup evidence, preview, and production approval", () => {
  const { source, value } = workflow("reset-test-catalog.yml");
  assert.equal(value.concurrency.group, "publication-catalog-mutation");
  assert.equal(value.jobs.preview.environment, "cloudflare-pages");
  assert.equal(value.jobs.approval.environment, "ebook-production");
  assert.deepEqual(value.jobs.promote.needs, "approval");
  assert.equal(value.jobs.promote.environment, "cloudflare-pages");
  assert.match(source, /backup_sha256/);
  assert.match(
    source,
    /catalog_reset\.py verify[\s\\\n]+--plan _catalog-reset-plan\.json[\s\\\n]+--remote/,
  );
  assert.match(source, /Wait for clean production deployment/);
  assert.match(source, /catalog_reset\.py finalize-remote/);
  assert.match(source, /cleanup-cloudflare-deployments\.mjs/);
});

test("all publication mutations share one repository-wide concurrency lock", () => {
  for (const name of [
    "ebook-candidate.yml",
    "remove-publication.yml",
    "reset-test-catalog.yml",
  ]) {
    assert.equal(
      workflow(name).value.concurrency.group,
      "publication-catalog-mutation",
    );
  }
});
