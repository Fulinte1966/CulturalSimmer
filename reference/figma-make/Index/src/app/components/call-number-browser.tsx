import { useMemo, useState } from "react";
import imgPages from "../../imports/Index/bed415caa8df8d0a09e50b2dc1031c35124978c8.png";
import Group13 from "../../imports/Group13";
import Borderline from "../../imports/Borderline-1";

type Node = {
  code: string;
  label: string;
  children?: Node[];
};

const TREE: Node = {
  code: "",
  label: "书目索引",
  children: [
    {
      code: "A",
      label: "马克思主义、列宁主义、毛泽东主义",
      children: [
        {
          code: "A1",
          label: "马克思、恩格斯著作",
          children: [
            { code: "A11", label: "选集、文集、选读" },
            { code: "A12", label: "单行著作" },
            { code: "A13", label: "书信集、日记、函电" },
            { code: "A15", label: "手迹" },
            { code: "A16", label: "专题汇编" },
            { code: "A18", label: "语录" },
          ],
        },
        { code: "A2", label: "列宁著作" },
        { code: "A3", label: "斯大林著作" },
        { code: "A4", label: "毛泽东著作" },
        { code: "A5", label: "马克思、恩格斯、列宁、斯大林、毛泽东著作汇编" },
        { code: "A6", label: "马克思、恩格斯、列宁、斯大林、毛泽东的生平和传记" },
        { code: "A7", label: "马克思主义、列宁主义、毛泽东主义的学习、研究和参考资料" },
      ],
    },
    { code: "B", label: "哲学" },
    { code: "C", label: "社会科学总论" },
    { code: "D", label: "政治" },
    { code: "F", label: "经济" },
    { code: "I", label: "文学" },
    { code: "K", label: "历史、地理" },
  ],
};

function buildMaps(root: Node) {
  const byCode = new Map<string, Node>();
  const parentOf = new Map<string, Node>();
  const walk = (n: Node, parent: Node | null) => {
    byCode.set(n.code, n);
    if (parent) parentOf.set(n.code, parent);
    n.children?.forEach((c) => walk(c, n));
  };
  walk(root, null);
  return { byCode, parentOf };
}

function ancestryPath(node: Node, parentOf: Map<string, Node>): Node[] {
  const path: Node[] = [];
  let cur: Node | undefined = node;
  while (cur && cur.code !== "") {
    path.unshift(cur);
    cur = parentOf.get(cur.code);
  }
  return path;
}

function splitCode(code: string) {
  // Highlight the last character of the code with black; the prefix greyed.
  if (code.length <= 1) return { prefix: "", tail: code };
  return { prefix: code.slice(0, -1), tail: code.slice(-1) };
}

const CODE_FONT = "font-['TeX_Gyre_Termes:Bold',_'Times_New_Roman',serif]";
const HEAVY_FONT = "font-['寒蝉锦书宋:Heavy',_'Songti_SC',serif]";
const MEDIUM_FONT = "font-['寒蝉锦书宋:TextMedium',_'Songti_SC',serif]";
const REGULAR_FONT = "font-['寒蝉锦书宋:TextRegular',_'Songti_SC',serif]";
const UI_FONT = "font-['LXGW_Neo_ZhiSong_Screen:Regular',_'Songti_SC',serif]";
const DISPLAY_FONT = "font-['Glow_Sans_SC:Compressed_ExtraBold',_sans-serif]";

function CodeCell({
  node,
  onClick,
  size = 36,
}: {
  node: Node;
  onClick: () => void;
  size?: number;
}) {
  const { prefix, tail } = splitCode(node.code);
  return (
    <button
      onClick={onClick}
      className={`${CODE_FONT} text-black text-center whitespace-nowrap leading-none cursor-pointer hover:opacity-60 transition-opacity bg-transparent border-0 p-0 justify-self-start self-center`}
      style={{ fontSize: size }}
      aria-label={`Browse ${node.code}`}
    >
      {prefix && <span className="text-[rgba(0,0,0,0.15)]">{prefix}</span>}
      <span>{tail}</span>
    </button>
  );
}

function LabelCell({
  node,
  onClick,
  variant,
}: {
  node: Node;
  onClick: () => void;
  variant: "heavy" | "medium" | "regular";
}) {
  const font =
    variant === "heavy" ? HEAVY_FONT : variant === "medium" ? MEDIUM_FONT : REGULAR_FONT;
  const size = variant === "heavy" ? 36 : variant === "medium" ? 32 : 24;
  const lh = variant === "heavy" ? "1.75" : variant === "medium" ? "1.5" : "1";
  return (
    <button
      onClick={onClick}
      className={`${font} text-black text-left cursor-pointer hover:opacity-60 transition-opacity bg-transparent border-0 p-0 justify-self-stretch self-center`}
      style={{ fontSize: size, lineHeight: lh, fontFeatureSettings: '"hwid"' }}
      aria-label={`Show results for ${node.code}`}
    >
      {node.label}
    </button>
  );
}

function variantFor(node: Node, parentOf: Map<string, Node>): "heavy" | "medium" | "regular" {
  // Root-level categories (single letter, parent is root) => heavy
  const parent = parentOf.get(node.code);
  if (!parent || parent.code === "") return "heavy";
  // Second level (parent is a root category) => medium
  const grand = parentOf.get(parent.code);
  if (!grand || grand.code === "") return "medium";
  return "regular";
}

function BookGrid({ count }: { count: number }) {
  return (
    <div className="grid grid-cols-5 gap-9">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="w-[168px] h-[238px] rounded-lg overflow-hidden flex items-center justify-center"
        >
          <img
            src={imgPages}
            alt="Book cover"
            className="w-full h-full object-cover"
            style={{ aspectRatio: "173/246" }}
          />
        </div>
      ))}
    </div>
  );
}

function today() {
  const d = new Date();
  const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
  return {
    date: `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`,
    day: `星期${weekdays[d.getDay()]}`,
  };
}

export function CallNumberBrowser() {
  const { byCode, parentOf } = useMemo(() => buildMaps(TREE), []);
  const [mode, setMode] = useState<"callnumber" | "keyword">("callnumber");
  const [keyword, setKeyword] = useState<string>("");
  const [browseCode, setBrowseCode] = useState<string>(""); // root
  const [selectedCode, setSelectedCode] = useState<string | null>(null);

  const browseNode = byCode.get(browseCode) ?? TREE;
  const selectedNode = selectedCode ? byCode.get(selectedCode) ?? null : null;

  const rows: Node[] = useMemo(() => {
    if (selectedNode) {
      return ancestryPath(selectedNode, parentOf);
    }
    // Browsing view: ancestry of browseNode (excluding root), then children of browseNode.
    if (browseNode.code === "") {
      return TREE.children ?? [];
    }
    const path = ancestryPath(browseNode, parentOf);
    const children = browseNode.children ?? [];
    return [...path, ...children];
  }, [browseNode, selectedNode, parentOf]);

  const handleCodeClick = (node: Node) => {
    // If clicking the code of the currently selected node, unfinalize and browse its parent.
    if (selectedNode && node.code === selectedNode.code) {
      const parent = parentOf.get(node.code);
      setSelectedCode(null);
      setBrowseCode(parent ? parent.code : "");
      return;
    }
    // If clicking the code of the current browseNode, go up one level.
    if (!selectedNode && node.code === browseNode.code && browseNode.code !== "") {
      const parent = parentOf.get(node.code);
      setBrowseCode(parent ? parent.code : "");
      setSelectedCode(null);
      return;
    }
    // Otherwise browse this node.
    setSelectedCode(null);
    setBrowseCode(node.code);
  };

  const handleLabelClick = (node: Node) => {
    setSelectedCode(node.code);
    setBrowseCode(node.code);
  };

  // Book grid visibility: at root browsing show none; otherwise show a sample grid.
  const showBooks =
    mode === "keyword"
      ? keyword.trim().length > 0
      : selectedNode !== null || browseNode.code !== "";
  const bookCount =
    mode === "keyword" ? (keyword.trim() ? 10 : 0) : selectedNode ? 10 : browseNode.code === "" ? 0 : 10;

  const toggleMode = () => {
    setMode((m) => (m === "callnumber" ? "keyword" : "callnumber"));
  };
  const modeLabel = mode === "callnumber" ? "书目索引" : "关键词";
  const modeLabelSize = mode === "callnumber" ? 17 : 22;
  const modeLabelTracking = mode === "callnumber" ? "1.7px" : "4.4px";

  const { date, day } = today();

  return (
    <div className="min-h-screen bg-white flex flex-col items-center">
      <div className="w-[1152px] pt-6 flex flex-col gap-6">
        {/* Head */}
        <div className="relative h-9 w-full">
          <div
            className={`${UI_FONT} absolute left-0 top-0 h-[18px] flex items-center text-[12px] text-black leading-none`}
          >
            <span>主页</span>
            <span>・</span>
            <span>索引</span>
          </div>
          <div className="absolute right-0 top-0 h-[18px] flex items-center gap-3">
            <div className={`${CODE_FONT} text-[12px] text-black tracking-wider`}>CR</div>
            <div className={`${UI_FONT} flex gap-3 text-[12px] text-black leading-none`}>
              <span>{date}</span>
              <span>{day}</span>
            </div>
          </div>
          <div className="absolute left-0 right-0 top-[25px] border-t-2 border-black" />
        </div>

        {/* Index bar */}
        <div className="w-full flex gap-[18px] items-start">
          <button
            onClick={toggleMode}
            className="flex items-start shrink-0 bg-transparent border-0 p-0 cursor-pointer hover:opacity-60 transition-opacity"
            aria-label={`Switch to ${mode === "callnumber" ? "keyword search" : "call-number browser"}`}
          >
            <div className="relative w-[108px] h-[62.5862px]">
              <Group13 text={mode === "keyword" ? "关键词" : "书目索引"} />
            </div>
          </button>
          <div className="flex-1 flex flex-col gap-6 items-start justify-center">
            <div className="w-full h-[12px] border-t-2 border-black"><Borderline /></div>
            {mode === "callnumber" ? (
              <div
                className="w-full pl-[18px] grid gap-x-9 gap-y-1"
                style={{ gridTemplateColumns: "fit-content(100%) minmax(0, 1fr)" }}
              >
                {rows.map((node) => {
                  const v = variantFor(node, parentOf);
                  const size = v === "heavy" ? 36 : v === "medium" ? 32 : 24;
                  return (
                    <div key={node.code} className="contents">
                      <CodeCell node={node} onClick={() => handleCodeClick(node)} size={size} />
                      <LabelCell node={node} onClick={() => handleLabelClick(node)} variant={v} />
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="w-full pl-[18px]">
                <input
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="请输入关键词检索"
                  className={`${HEAVY_FONT} w-full bg-transparent border-0 outline-none text-black placeholder:text-[rgba(0,0,0,0.15)] leading-none`}
                  style={{ fontSize: 36 }}
                />
              </div>
            )}
            <div className="w-full h-[12px] border-t-2 border-black"><Borderline /></div>
          </div>
        </div>

        {/* Book grid */}
        {showBooks && (
          <div className="flex flex-col items-center gap-6 pb-12">
            <BookGrid count={bookCount} />
            <p className={`${UI_FONT} text-[12px] text-black`}>
              首页　上一页　第 1 页　共 2 页　下一页　尾页
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
