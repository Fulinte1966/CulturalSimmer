import fs from "node:fs";
import path from "node:path";
import { parse } from "yaml";

export interface ClassificationNode {
  code: string;
  label: string;
  parentCode?: string;
  depth: number;
  children: ClassificationNode[];
}

interface ClassificationSourceNode {
  code: string;
  label: string;
  children?: ClassificationSourceNode[];
}

interface ClassificationDocument {
  schemaVersion: number;
  classifications: ClassificationSourceNode[];
}

const SOURCE_CLASSIFICATION_CODE = /^[A-Z]\d*$/;

let treeCache: ClassificationNode[] | null = null;
let flatCache: Map<string, ClassificationNode> | null = null;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function formatClassificationCode(sourceCode: string): string {
  if (!SOURCE_CLASSIFICATION_CODE.test(sourceCode)) {
    throw new Error(`Invalid source classification code: ${sourceCode}`);
  }

  const prefix = sourceCode[0];
  const digits = sourceCode.slice(1);
  const groups = digits.match(/.{1,3}/g) ?? [];
  return `${prefix}${groups.join(".")}`;
}

function readDocument(): ClassificationDocument {
  const filePath = path.join(process.cwd(), "src", "data", "classifications.yml");
  const document = parse(fs.readFileSync(filePath, "utf-8")) as unknown;

  if (!isRecord(document) || document.schemaVersion !== 1) {
    throw new Error("classifications.yml must use schemaVersion: 1");
  }
  if (!Array.isArray(document.classifications)) {
    throw new Error("classifications.yml classifications must be a sequence");
  }

  return document as unknown as ClassificationDocument;
}

function buildTree(sourceNodes: ClassificationSourceNode[]): ClassificationNode[] {
  const seen = new Set<string>();

  const buildNode = (
    source: ClassificationSourceNode,
    parentSourceCode: string | undefined,
    parentCode: string | undefined,
    depth: number,
  ): ClassificationNode => {
    if (!isRecord(source)) {
      throw new Error("Every classification entry must be a mapping");
    }

    const { code, label, children } = source;
    if (typeof code !== "string" || !SOURCE_CLASSIFICATION_CODE.test(code)) {
      throw new Error(`Invalid source classification code: ${String(code)}`);
    }
    if (typeof label !== "string" || label.trim() === "") {
      throw new Error(`Classification ${code} requires a non-empty label`);
    }
    if (seen.has(code)) {
      throw new Error(`Duplicate classification code: ${code}`);
    }
    if (parentSourceCode && !code.startsWith(parentSourceCode)) {
      throw new Error(
        `Classification ${code} must start with parent code ${parentSourceCode}`,
      );
    }
    if (children !== undefined && !Array.isArray(children)) {
      throw new Error(`Classification ${code} children must be a sequence`);
    }

    seen.add(code);
    const formattedCode = formatClassificationCode(code);
    return {
      code: formattedCode,
      label: label.trim(),
      parentCode,
      depth,
      children: (children ?? []).map((child) =>
        buildNode(child, code, formattedCode, depth + 1),
      ),
    };
  };

  return sourceNodes.map((source) => buildNode(source, undefined, undefined, 1));
}

function ensureTree(): void {
  if (treeCache && flatCache) return;

  treeCache = buildTree(readDocument().classifications);
  flatCache = new Map();

  const visit = (nodes: ClassificationNode[]) => {
    for (const node of nodes) {
      flatCache!.set(node.code, node);
      visit(node.children);
    }
  };
  visit(treeCache);
}

export function getClassificationNodes(): ClassificationNode[] {
  ensureTree();
  return treeCache!;
}

export function getFlatClassificationMap(): Map<string, ClassificationNode> {
  ensureTree();
  return flatCache!;
}

export function getTopLevelClassifications(): ClassificationNode[] {
  return getClassificationNodes();
}

export function getClassificationNode(code: string): ClassificationNode | undefined {
  return getFlatClassificationMap().get(code);
}

export function getClassificationAncestors(code: string): ClassificationNode[] {
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
  return getClassificationNode(code)?.label ?? code;
}
