import fs from "node:fs";
import path from "node:path";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ClassificationNode {
  code: string;
  label: string;
  parentCode?: string;
  depth: number;
  children: ClassificationNode[];
}

// ---------------------------------------------------------------------------
// Cache
// ---------------------------------------------------------------------------

let _treeCache: ClassificationNode[] | null = null;
let _flatCache: Map<string, ClassificationNode> | null = null;

// ---------------------------------------------------------------------------
// YAML loader
// ---------------------------------------------------------------------------

function loadYaml(): Map<string, string> {
  const filePath = path.join(
    process.cwd(),
    "src",
    "data",
    "classifications.yml"
  );
  const content = fs.readFileSync(filePath, "utf-8");
  const map = new Map<string, string>();

  for (const line of content.split(/\r?\n/)) {
    const match = line.match(/^([A-Z](?:\d+(?:\.\d+)?)?):\s*(.+)$/);
    if (match) {
      map.set(match[1], match[2].trim());
    }
  }

  return map;
}

// ---------------------------------------------------------------------------
// Tree builder
// ---------------------------------------------------------------------------

function buildTree(entries: Map<string, string>): ClassificationNode[] {
  const nodes = new Map<string, ClassificationNode>();
  const roots: ClassificationNode[] = [];

  // Create nodes for every classification key
  for (const [code, label] of entries) {
    nodes.set(code, {
      code,
      label,
      depth: 0, // computed below
      children: [],
    });
  }

  // Link parent-child relationships
  for (const code of entries.keys()) {
    const node = nodes.get(code)!;
    const parentCode = findParentCode(code, entries);

    if (parentCode) {
      const parent = nodes.get(parentCode);
      if (parent) {
        node.parentCode = parentCode;
        node.depth = parent.depth + 1;
        parent.children.push(node);
        continue;
      }
    }

    // No parent found — top-level node
    node.depth = 1;
    roots.push(node);
  }

  // Sort children by YAML source order (the insertion order from the Map
  // preserves the original file order, so just sort roots).
  roots.sort((a, b) => sortBySourceOrder(a.code, b.code, entries));

  return roots;
}

/** Find the longest existing proper code prefix of *code*. */
function findParentCode(
  code: string,
  entries: Map<string, string>
): string | undefined {
  // Strip characters from the right until we find a known code.
  for (let i = code.length - 1; i > 0; i--) {
    const candidate = code.slice(0, i);
    if (candidate !== code && entries.has(candidate)) {
      return candidate;
    }
  }
  return undefined;
}

function sortBySourceOrder(
  a: string,
  b: string,
  entries: Map<string, string>
): number {
  // Order by position in the YAML file
  const keys = [...entries.keys()];
  const ai = keys.indexOf(a);
  const bi = keys.indexOf(b);
  if (ai !== -1 && bi !== -1) return ai - bi;
  return a.localeCompare(b);
}

// ---------------------------------------------------------------------------
// Lazy init
// ---------------------------------------------------------------------------

function ensureTree(): void {
  if (_treeCache && _flatCache) return;

  const entries = loadYaml();
  _treeCache = buildTree(entries);

  // Build flat lookup
  _flatCache = new Map();
  const stack = [..._treeCache];
  while (stack.length > 0) {
    const node = stack.pop()!;
    _flatCache.set(node.code, node);
    stack.push(...node.children);
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function getClassificationNodes(): ClassificationNode[] {
  ensureTree();
  return _treeCache!;
}

export function getFlatClassificationMap(): Map<string, ClassificationNode> {
  ensureTree();
  return _flatCache!;
}

export function getTopLevelClassifications(): ClassificationNode[] {
  ensureTree();
  return _treeCache!;
}

export function getClassificationNode(
  code: string
): ClassificationNode | undefined {
  ensureTree();
  return _flatCache!.get(code);
}

export function getClassificationAncestors(
  code: string
): ClassificationNode[] {
  const result: ClassificationNode[] = [];
  let current = getClassificationNode(code);
  while (current?.parentCode) {
    const parent = getClassificationNode(current.parentCode);
    if (!parent) break;
    result.push(parent);
    current = parent;
  }
  return result;
}

export function getClassificationLabel(code: string): string {
  const node = getClassificationNode(code);
  return node?.label ?? code;
}
