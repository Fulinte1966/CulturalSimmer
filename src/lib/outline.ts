export interface OutlineItem {
  level: number;
  title: string;
}

const outlinePunctuation: Readonly<Record<string, string>> = {
  "、": ",",
  "。": ".",
  "，": ",",
  "：": ":",
  "；": ";",
  "！": "!",
  "？": "?",
  "（": "(",
  "）": ")",
  "［": "[",
  "］": "]",
  "【": "[",
  "】": "]",
  "｛": "{",
  "｝": "}",
  "“": '"',
  "”": '"',
  "‘": "'",
  "’": "'",
  "《": "<",
  "》": ">",
  "〈": "<",
  "〉": ">",
  "「": '"',
  "」": '"',
  "『": "'",
  "』": "'",
  "・": "·",
};

/** 仅规范详情页目录大纲的显示文本，不改写 PDF 书签派生数据。 */
export function normalizeOutlinePunctuation(title: string): string {
  return title
    .replace(/……+/gu, "...")
    .replace(/——+/gu, "--")
    .replace(/[\uFF01-\uFF5E]/gu, (character) =>
      String.fromCharCode(character.charCodeAt(0) - 0xfee0)
    )
    .replace(/\u3000/gu, " ")
    .replace(/[、。，：；！？（）［］【】｛｝“”‘’《》〈〉「」『』・]/gu, (character) =>
      outlinePunctuation[character] ?? character
    );
}
