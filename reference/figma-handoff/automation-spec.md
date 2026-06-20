# GitHub automation specification

## User workflow

The supported intake mechanism is a GitHub Release:

1. Create a temporary Release tag named `ingest-YYYYMMDD-HHMM`.
2. Attach exactly one PDF.
3. Publish the Release.

The temporary Release title and PDF filename are not data sources. Canonical
identity comes from validated PDF XMP.

GitHub itself requires creating and publishing the Release; after that action,
no Markdown, JSON, cover, tag, filename, or deployment work is manual.

## Workflow trigger

Add `.github/workflows/ingest-pdf.yml`:

```yaml
on:
  release:
    types: [published]
```

The job runs only when the tag begins with `ingest-`. Canonical Releases must
exit immediately so creating them does not create an ingestion loop.

Use a single non-cancelling `pdf-ingest` concurrency group.

## Permissions and runtime

- `contents: write`
- Ubuntu runner
- Node 22
- Python 3.12
- repository `GITHUB_TOKEN` passed to `gh`

Pin runtime dependencies in a repository requirements file. Required Python
capabilities are PyMuPDF, safe XML parsing, and safe YAML serialization.

Do not use third-party release-upload Actions when the preinstalled `gh` CLI
and GitHub API provide the operation.

## Processing transaction

1. Check out `main` with enough history to pull and push safely.
2. Download all assets from the intake Release into an isolated workspace.
3. Require exactly one file with a `.pdf` extension.
4. Calculate SHA-256 before processing.
5. Extract and strictly validate the metadata contract.
6. Calculate canonical tag and filename.
7. Reject duplicates before writing generated files.
8. Generate Markdown, manifest, cover, spine, outline, and reading JSON.
9. Run metadata tests, reading tests, UI tests, validation, Astro check, and
   production build.
10. Create the canonical Release and upload the normalized PDF name.
11. Commit generated files as `github-actions[bot]` and push to `main`.
12. Only after push succeeds, delete the temporary Release and temporary tag.
13. The push triggers the existing Pages deployment workflow.

No metadata value may be interpolated into a shell program. Pass values as
arguments or structured files and validate identifiers before GitHub API use.

## Duplicate policy

The identity key is `call number + edition`.

Reject without overwrite when any of these exists:

- canonical GitHub Release;
- canonical Git tag;
- `src/content/books/{id}.md` with the same edition;
- canonical manifest;
- canonical cover, outline, or reading file.

The failed intake Release remains available for logs and manual cleanup. The
workflow must not silently replace an already published PDF.

## Failure and rollback

- Metadata, validation, test, or build failure: create no canonical Release and
  push no commit.
- Duplicate failure: make no repository or canonical Release changes.
- Canonical Release creation succeeds but push fails: delete the canonical
  Release and canonical tag, then leave the intake Release intact.
- Cleanup failure after a successful push: do not roll back the published book;
  report the stale intake Release in the Action summary.
- Never use force push.

Emit a GitHub Actions job summary containing the book ID, edition, SHA-256,
generated paths, canonical tag, and failure stage without dumping raw XMP.

## Generated commit

Suggested message:

```text
content: ingest F0-1-1 edition 1
```

The commit contains only generated book entry, manifest, cover/spine, outline,
and reading files. It must not include the downloaded PDF.

## Pages workflow

Normalize the repository default branch and workflow trigger to `main` before
enabling ingestion. The current local branch and existing deployment workflow
must not remain contradictory.

Pages build runs:

```text
npm ci
npm run test:ui
npm run validate
npm run check
npm run build
```

Python extraction tests belong in the ingestion job; static deployment does
not need PyMuPDF to read already generated data.

## Branch protection assumption

Full automation requires `github-actions[bot]` to push generated commits to
`main`. If branch protection forbids that, use a GitHub App or an auto-merge PR
workflow; do not weaken validation or use a personal access token embedded in
the repository.

## Local safety

Implementation and dry runs must not create, edit, publish, or delete real
Releases. Isolate GitHub side effects behind explicit CLI commands and test the
pipeline with fixture PDFs and mocked release metadata.

