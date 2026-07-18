import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { parse as parseYaml } from "yaml";

const root = path.resolve(new URL("../..", import.meta.url).pathname);

function workflow(name: string) {
  const source = fs.readFileSync(path.join(root, ".github/workflows", name), "utf8");
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

test("ordinary deployment does not dispatch reader notifications", () => {
  const { source } = workflow("deploy.yml");
  assert.doesNotMatch(source, /notify_updates|notify\.yml|notify-ntfy\.yml/);
});
