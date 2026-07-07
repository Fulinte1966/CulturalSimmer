# CulturalSimmer Errata Workflow Skill

## Purpose

This skill maintains the CulturalSimmer reader errata and website bug reporting workflow.

The workflow connects:

```text
Website book detail page
→ Tally reader errata form
→ Make.com webhook scenario
→ GitHub Issue creation
→ GitHub Actions workflow
→ GitHub Project routing and field population
```

There are two issue types:

```text
书籍勘误 → created by Tally/Make only
网站捉虫 → created through GitHub Issue Form
```

The project intentionally keeps labels minimal:

```text
书籍勘误
网站捉虫
```

Status should be handled by the GitHub Project `Status` field, not by issue labels.

---

## Current repository

```text
Repository: Fulinte1966/CulturalSimmer
Default branch: main
Public repository
```

Important paths:

```text
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/website-bug.yml
.github/workflows/route-issue-to-project.yml
```

---

## Design principles

1. Do not allow GitHub-native book errata submissions.
2. Book errata must go through Tally so `bookId` and `edition` can be passed as hidden fields.
3. GitHub Issue Forms should be used only for website bugs.
4. Labels identify issue type only.
5. Project `Status` identifies process state.
6. Project field `索书号` stores:
   - actual call number for book errata, e.g. `F0-1-1`
   - fixed value `网站捉虫` for website bug issues
7. Do not rewrite issue titles in GitHub Actions.
8. The Make-generated issue title remains the source of submission traceability.

---

## Tally form

Current Tally form:

```text
https://tally.so/r/XxyDOP
```

The form has hidden fields:

```text
bookId
edition
```

Book detail pages should open Tally with query parameters:

```text
https://tally.so/r/XxyDOP?bookId=F0-1-1&edition=1
```

If the bare Tally URL is opened directly, hidden fields may be `null`, so the GitHub Issue Template contact link should not point directly to the bare Tally form unless this limitation is acceptable.

Recommended public entry behavior:

```text
GitHub New issue → 书籍勘误 contact link → website/book detail page
Website/book detail page → 勘误 button → Tally URL with bookId and edition
```

---

## Tally Thank You page

Tally Thank You page cannot reliably create a dynamic clickable URL containing `@Submission ID`.

Best lightweight solution:

Display the generated `@Submission ID` and provide a plain-text GitHub search URL with `@Submission ID` appended.

Recommended Thank You page text:

```text
提交成功。

提交号：@Submission ID

系统将自动生成公开处理记录。生成可能需要数秒；若打开后暂时没有结果，请稍后刷新。

请复制并访问：

https://github.com/Fulinte1966/CulturalSimmer/issues?q=is%3Aissue%20in%3Atitle%20@Submission ID
```

This works because Make creates issue titles like:

```text
F0-1-1_v1: J1J2MQo
```

The GitHub search URL finds the issue by `submissionId` in the title.

---

## Make.com scenario

Scenario shape:

```text
Tally webhook
→ Make Custom Webhook
→ HTTP Make a request
→ GitHub REST API: Create Issue
```

Use HTTP instead of Make’s GitHub module to avoid unnecessary GitHub integration scopes.

### GitHub REST API endpoint

```text
POST https://api.github.com/repos/Fulinte1966/CulturalSimmer/issues
```

### Auth

Use Make HTTP API key auth:

```text
Placement: Header
Parameter name: Authorization
Value: Bearer <GitHub PAT>
```

### Headers

```text
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

### Body mode

```text
Body type: application/json
Body input method: Data structure
```

Fields:

```text
title: Text
body: Text
labels: Array of Text
```

### Labels for book errata

Use only:

```json
[
  "书籍勘误"
]
```

Do not use older labels:

```text
类型：书籍勘误
状态：待核查
```

### Title format

Use this Make expression:

```make
{{ifempty(8.data.fields[1].value; "MISSING-BOOKID")}}_v{{ifempty(8.data.fields[2].value; "MISSING-EDITION")}}: {{8.data.submissionId}}
```

Expected output:

```text
F0-1-1_v1: J1J2MQo
```

Do not replace the submission ID with the GitHub issue number. The GitHub issue already has its own number; the Tally submission ID is more useful for tracing the original form response.

### Body format

Recommended body:

```markdown
## 读者勘误表

索书号：{{ifempty(8.data.fields[1].value; "MISSING-BOOKID")}}
版本号：{{ifempty(8.data.fields[2].value; "MISSING-EDITION")}}
出版号：{{ifempty(8.data.fields[1].value; "MISSING-BOOKID")}}_v{{ifempty(8.data.fields[2].value; "MISSING-EDITION")}}

---

### 位置

{{switch(8.data.fields[3].value[1]; "e7c78a4c-0640-4389-9b2e-871c430ff689"; "外表及前置部分"; "1011c10d-7410-4214-a0f2-d1642ac08faa"; "正文及后附部分"; "未知位置")}}

{{if(ifempty(8.data.fields[4].value; "__EMPTY__") = "__EMPTY__"; emptystring; "### 页码

" + 8.data.fields[4].value)}}

### 勘误内容

{{8.data.fields[5].value}}

> 表单号：{{8.data.formId}}
> 提交号：{{8.data.submissionId}}
> 读者号：{{8.data.respondentId}}
> 提交时间：{{formatDate(8.data.createdAt; "YYYY-MM-DD HH:mm:ss"; "Asia/Shanghai")}} UTC+8
```

Do not include Tally `submissionPdfUrl` or `submissionPreviewUrl` in public GitHub issues because they may contain tokens/signatures.

### Make field-index assumptions

The current Make setup uses direct fixed-index references:

```text
{{8.data.fields[1].value}} = bookId
{{8.data.fields[2].value}} = edition
{{8.data.fields[3].value[1]}} = location option ID
{{8.data.fields[4].value}} = page
{{8.data.fields[5].value}} = content
```

Make array indexing is 1-based in this context.

This is acceptable only while Tally field order remains stable.

---

## GitHub Issue Template configuration

### `.github/ISSUE_TEMPLATE/config.yml`

Book errata should not have a GitHub-native form. Use a contact link instead.

Recommended:

```yaml
blank_issues_enabled: false

contact_links:
  - name: 书籍勘误
    url: https://github.com/Fulinte1966/CulturalSimmer
    about: 请前往网站书目详情页，点击右上角的［勘误］填写《读者勘误表》；系统会自动关联索书号和版本号。
```

If the website URL is stable, prefer replacing the URL with the actual site/book index URL:

```yaml
url: https://fulinte1966.github.io/CulturalSimmer/
```

Do not point this link to the bare Tally form unless it is acceptable for hidden fields to be missing.

---

## Website bug Issue Form

### `.github/ISSUE_TEMPLATE/website-bug.yml`

Use this final template:

```yaml
name: 网站捉虫
description: 指出网站功能上存在的问题或可改进的地方。
title: "[网站捉虫] "
labels:
  - 网站捉虫

body:
  - type: dropdown
    id: category
    attributes:
      label: 问题类型
      options:
        - 下载问题
        - 链接失效
        - 页面显示异常
        - 搜索或索引问题
        - 字体或排版显示问题
        - 移动端适配问题
        - 其他问题
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      placeholder: ［示例］点击某本书的下载按钮后没有反应……
    validations:
      required: true

  - type: input
    id: page_url
    attributes:
      label: 出错页面
      placeholder: https://...
    validations:
      required: false

  - type: textarea
    id: steps
    attributes:
      label: 复现步骤
      placeholder: |
        1. 打开……
        2. 点击……
        3. 看到……
    validations:
      required: false

  - type: textarea
    id: actual
    attributes:
      label: 实际表现
      placeholder: ［示例］页面空白、按钮无响应、文字重叠……
    validations:
      required: false

  - type: textarea
    id: expected
    attributes:
      label: 预期表现
      placeholder: ［示例］应正常下载 PDF……
    validations:
      required: false

  - type: textarea
    id: screenshots
    attributes:
      label: 截图或录屏
      placeholder: 请将媒体文件粘贴或拖入此处
    validations:
      required: false

  - type: textarea
    id: environment
    attributes:
      label: 环境信息
      placeholder: |
        浏览器：Chrome / Safari / Firefox / Edge / ...
        系统：Windows / macOS / iOS / Android / ...
        设备：电脑 / 手机 / 平板 / ...
    validations:
      required: false
```

---

## GitHub Project

Project owner:

```text
Fulinte1966
```

Project number currently used:

```text
1
```

Project URL pattern:

```text
https://github.com/users/Fulinte1966/projects/1
```

Required field:

```text
索书号
```

Field type:

```text
Text
```

Recommended Status field values:

```text
待核查
核查中
已确认
已修正
不采纳
```

Project `Status` should be set by GitHub Project built-in workflow:

```text
When item added to project → Set Status to 待核查
```

Do not duplicate status as issue labels.

---

## GitHub Actions token

Create a classic PAT:

```text
GitHub
→ Settings
→ Developer settings
→ Personal access tokens
→ Tokens (classic)
→ Generate new token (classic)
```

Token note:

```text
CulturalSimmer Project Automation
```

Scopes:

```text
project
```

If the repository becomes private, add:

```text
repo
```

Save token as repository secret:

```text
Repository Settings
→ Secrets and variables
→ Actions
→ New repository secret

Name: PROJECT_TOKEN
Value: <classic PAT>
```

Do not use fine-grained PAT for this specific personal Project workflow if it fails to access user-owned Projects.

---

## GitHub Actions workflow

### `.github/workflows/route-issue-to-project.yml`

This workflow uses GraphQL via `gh api graphql`.

Do not use `gh project view`, `gh project item-add`, or `gh project item-edit` here because the CLI owner resolution caused failures in GitHub Actions:

```text
unknown owner type
owner is required when not running interactively
```

Final workflow:

```yaml
name: Route issue to project

on:
  issues:
    types:
      - opened

permissions:
  contents: read

concurrency:
  group: route-issue-${{ github.event.issue.number }}
  cancel-in-progress: false

jobs:
  route-issue:
    runs-on: ubuntu-latest

    env:
      PROJECT_OWNER: "Fulinte1966"
      PROJECT_NUMBER: "1"
      CALL_NUMBER_FIELD_NAME: "索书号"
      BOOK_ERRATA_LABEL: "书籍勘误"
      WEBSITE_BUG_LABEL: "网站捉虫"

    steps:
      - name: Detect issue type
        id: detect
        shell: bash
        run: |
          set -euo pipefail

          labels="$(jq -r '[.issue.labels[].name] | @json' "$GITHUB_EVENT_PATH")"

          has_book_errata=false
          has_website_bug=false

          if jq -e --arg label "$BOOK_ERRATA_LABEL" 'index($label)' <<< "$labels" > /dev/null; then
            has_book_errata=true
          fi

          if jq -e --arg label "$WEBSITE_BUG_LABEL" 'index($label)' <<< "$labels" > /dev/null; then
            has_website_bug=true
          fi

          if [ "$has_book_errata" = true ] && [ "$has_website_bug" = true ]; then
            echo "issue_type=ambiguous" >> "$GITHUB_OUTPUT"
          elif [ "$has_book_errata" = true ]; then
            echo "issue_type=book-errata" >> "$GITHUB_OUTPUT"
          elif [ "$has_website_bug" = true ]; then
            echo "issue_type=website-bug" >> "$GITHUB_OUTPUT"
          else
            echo "issue_type=unknown" >> "$GITHUB_OUTPUT"
          fi

      - name: Stop if issue has no supported label
        if: steps.detect.outputs.issue_type == 'unknown'
        shell: bash
        run: |
          echo "No supported label found. Expected: $BOOK_ERRATA_LABEL or $WEBSITE_BUG_LABEL."
          echo "Skip routing."

      - name: Stop if issue has ambiguous labels
        if: steps.detect.outputs.issue_type == 'ambiguous'
        shell: bash
        run: |
          echo "Issue has both labels: $BOOK_ERRATA_LABEL and $WEBSITE_BUG_LABEL."
          echo "Skip routing."

      - name: Get project ID
        id: project
        if: steps.detect.outputs.issue_type == 'book-errata' || steps.detect.outputs.issue_type == 'website-bug'
        shell: bash
        env:
          GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}
        run: |
          set -euo pipefail

          project_id="$(
            gh api graphql \
              -f query='
                query($owner: String!, $number: Int!) {
                  user(login: $owner) {
                    projectV2(number: $number) {
                      id
                    }
                  }
                }
              ' \
              -f owner="$PROJECT_OWNER" \
              -F number="$PROJECT_NUMBER" \
              --jq '.data.user.projectV2.id'
          )"

          if [ -z "$project_id" ] || [ "$project_id" = "null" ]; then
            echo "Could not find user project: $PROJECT_OWNER / $PROJECT_NUMBER"
            exit 1
          fi

          echo "project_id=$project_id" >> "$GITHUB_OUTPUT"
          echo "Project ID found."

      - name: Add issue to project
        id: item
        if: steps.detect.outputs.issue_type == 'book-errata' || steps.detect.outputs.issue_type == 'website-bug'
        shell: bash
        env:
          GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}
        run: |
          set -euo pipefail

          content_id="$(jq -r '.issue.node_id' "$GITHUB_EVENT_PATH")"

          item_id="$(
            gh api graphql \
              -f query='
                mutation($projectId: ID!, $contentId: ID!) {
                  addProjectV2ItemById(input: {
                    projectId: $projectId
                    contentId: $contentId
                  }) {
                    item {
                      id
                    }
                  }
                }
              ' \
              -f projectId="${{ steps.project.outputs.project_id }}" \
              -f contentId="$content_id" \
              --jq '.data.addProjectV2ItemById.item.id'
          )"

          if [ -z "$item_id" ] || [ "$item_id" = "null" ]; then
            echo "Could not add issue to project."
            exit 1
          fi

          echo "item_id=$item_id" >> "$GITHUB_OUTPUT"
          echo "Issue added to project."

      - name: Decide call number value
        id: call_number
        if: steps.detect.outputs.issue_type == 'book-errata' || steps.detect.outputs.issue_type == 'website-bug'
        shell: bash
        run: |
          set -euo pipefail

          issue_type="${{ steps.detect.outputs.issue_type }}"

          if [ "$issue_type" = "website-bug" ]; then
            echo "skip=false" >> "$GITHUB_OUTPUT"
            echo "value=网站捉虫" >> "$GITHUB_OUTPUT"
            echo "网站捉虫 issue: set 索书号 field to 网站捉虫."
            exit 0
          fi

          title="$(jq -r '.issue.title // ""' "$GITHUB_EVENT_PATH")"
          body="$(jq -r '.issue.body // ""' "$GITHUB_EVENT_PATH")"

          book_id=""

          if [[ "$title" =~ ^([^_[:space:]]+)_v[^:[:space:]]+: ]]; then
            book_id="${BASH_REMATCH[1]}"
          fi

          if [ -z "$book_id" ]; then
            book_id="$(
              printf '%s\n' "$body" |
              sed -nE 's/^索书号：[[:space:]]*(.+)$/\1/p' |
              head -n 1 |
              sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
            )"
          fi

          if [ -z "$book_id" ] || [[ "$book_id" == MISSING* ]]; then
            echo "skip=true" >> "$GITHUB_OUTPUT"
            echo "value=" >> "$GITHUB_OUTPUT"
            echo "Book ID missing or invalid. Skip setting 索书号 field."
            exit 0
          fi

          echo "skip=false" >> "$GITHUB_OUTPUT"
          echo "value=$book_id" >> "$GITHUB_OUTPUT"
          echo "索书号 extracted: $book_id"

      - name: Get call number field ID
        id: call_number_field
        if: steps.call_number.outputs.skip != 'true'
        shell: bash
        env:
          GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}
        run: |
          set -euo pipefail

          response="$(
            gh api graphql \
              -f query='
                query($projectId: ID!) {
                  node(id: $projectId) {
                    ... on ProjectV2 {
                      fields(first: 100) {
                        nodes {
                          ... on ProjectV2FieldCommon {
                            id
                            name
                          }
                        }
                      }
                    }
                  }
                }
              ' \
              -f projectId="${{ steps.project.outputs.project_id }}"
          )"

          field_id="$(
            jq -r --arg name "$CALL_NUMBER_FIELD_NAME" \
              '.data.node.fields.nodes[] | select(.name == $name) | .id' \
              <<< "$response"
          )"

          if [ -z "$field_id" ] || [ "$field_id" = "null" ]; then
            echo "Could not find project field: $CALL_NUMBER_FIELD_NAME"
            exit 1
          fi

          echo "field_id=$field_id" >> "$GITHUB_OUTPUT"
          echo "索书号 field ID found."

      - name: Set call number project field
        if: steps.call_number.outputs.skip != 'true'
        shell: bash
        env:
          GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}
        run: |
          set -euo pipefail

          gh api graphql \
            -f query='
              mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $text: String!) {
                updateProjectV2ItemFieldValue(input: {
                  projectId: $projectId
                  itemId: $itemId
                  fieldId: $fieldId
                  value: {
                    text: $text
                  }
                }) {
                  projectV2Item {
                    id
                  }
                }
              }
            ' \
            -f projectId="${{ steps.project.outputs.project_id }}" \
            -f itemId="${{ steps.item.outputs.item_id }}" \
            -f fieldId="${{ steps.call_number_field.outputs.field_id }}" \
            -f text="${{ steps.call_number.outputs.value }}"

          echo "索书号 field updated: ${{ steps.call_number.outputs.value }}"
```

---

## Testing procedure

### Test website bug

1. Open GitHub repository.
2. Click `New issue`.
3. Choose `网站捉虫`.
4. Submit a test issue.
5. Expected:
   - label: `网站捉虫`
   - issue added to Project
   - Project field `索书号` = `网站捉虫`
   - Project Status set by Project workflow to `待核查`

### Test book errata

1. Open a book detail page.
2. Click the errata button.
3. Submit Tally.
4. Make creates GitHub issue.
5. Expected:
   - label: `书籍勘误`
   - title like `F0-1-1_v1: J1J2MQo`
   - issue added to Project
   - Project field `索书号` = `F0-1-1`
   - Project Status set by Project workflow to `待核查`

---

## Common failure modes

### Old workflow runs still use old YAML

Re-running an old failed workflow run uses the old commit and old workflow file. To test new YAML, create a new issue or trigger a new event after committing changes.

### Duplicate workflow runs

If trigger includes both:

```yaml
opened
labeled
```

a newly opened issue with labels may trigger two workflow runs.

Final trigger should be:

```yaml
on:
  issues:
    types:
      - opened
```

### `unknown owner type`

This happened with:

```bash
gh project view "$PROJECT_NUMBER" --owner "$PROJECT_OWNER"
```

Avoid `gh project` subcommands in Actions. Use GraphQL through `gh api graphql`.

### `owner is required when not running interactively`

This happened when trying:

```bash
gh project view "$PROJECT_NUMBER"
```

Again, avoid `gh project` subcommands in Actions. Use GraphQL.

### Could not find project

Check:

```text
PROJECT_OWNER
PROJECT_NUMBER
PROJECT_TOKEN
```

Make sure Project URL matches:

```text
https://github.com/users/Fulinte1966/projects/1
```

### Could not find field

Check Project field name exactly equals:

```text
索书号
```

No extra spaces.

### Book ID missing

Check Make title:

```text
F0-1-1_v1: J1J2MQo
```

or Make body line:

```text
索书号：F0-1-1
```

Also check Tally hidden fields are passed in the URL:

```text
?bookId=F0-1-1&edition=1
```

---

## Maintenance notes

1. If labels change, update both Issue Form and workflow env.
2. If Project number changes, update `PROJECT_NUMBER`.
3. If Project field `索书号` changes name, update `CALL_NUMBER_FIELD_NAME`.
4. If Tally field order changes, update Make field indexes.
5. If repository becomes private, regenerate `PROJECT_TOKEN` with `repo + project`.
6. Keep Tally submission ID in issue title for traceability.
7. Do not add status labels unless the Project `Status` model is removed.
