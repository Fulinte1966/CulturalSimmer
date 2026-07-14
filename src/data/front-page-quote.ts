export type FrontPageQuoteTextAlign = "left" | "center" | "right";

export interface FrontPageQuoteLine {
  text: string;
  hangingPunctuation?: string;
}

export interface FrontPageQuoteTypography {
  fontFamily: string;
  fontSizePx: number;
  fontWeight: number;
  letterSpacingPx: number;
  lineHeightPx: number;
  paddingBlockPx: number;
  paddingInlinePx: number;
}

export interface FrontPageQuoteLabelTypography {
  fontFamily: string;
  fontWeight: number;
  maxFontSizePx: number;
  maxBlockHeightPx: number;
  widthPx: number;
  gapPx: number;
  insetBlockPx: number;
  opticalOffsetXEm: number;
}

export interface FrontPageQuoteConfig {
  compactMaxWidthPx: number;
  label: string;
  lines: FrontPageQuoteLine[];
  maxWidthPx: number;
  textAlign: FrontPageQuoteTextAlign;
  typography: {
    regular: FrontPageQuoteTypography;
    compact: FrontPageQuoteTypography;
  };
  labelTypography: {
    regular: FrontPageQuoteLabelTypography;
    compact: FrontPageQuoteLabelTypography;
  };
}

export const frontPageQuote: FrontPageQuoteConfig = {
  compactMaxWidthPx: 416,
  label: "毛主席语录",
  maxWidthPx: 528,
  textAlign: "left",
  lines: [
    {
      text: "　　你们要关心国家大事",
      hangingPunctuation: "，",
    },
    { text: "要把无产阶级文化大革命" },
    { text: "进行到底！" },
  ],
  typography: {
    regular: {
      fontFamily: "var(--font-display-compact)",
      fontSizePx: 32,
      fontWeight: 400,
      letterSpacingPx: 8,
      lineHeightPx: 40,
      paddingBlockPx: 11,
      paddingInlinePx: 32,
    },
    compact: {
      fontFamily: "var(--font-display-compact)",
      fontSizePx: 22,
      fontWeight: 400,
      letterSpacingPx: 4,
      lineHeightPx: 28,
      paddingBlockPx: 8,
      paddingInlinePx: 22,
    },
  },
  labelTypography: {
    regular: {
      fontFamily: "var(--font-display-wide)",
      fontWeight: 700,
      maxFontSizePx: 20,
      maxBlockHeightPx: 21,
      widthPx: 30,
      gapPx: 6,
      insetBlockPx: 6,
      opticalOffsetXEm: 0,
    },
    compact: {
      fontFamily: "var(--font-display-wide)",
      fontWeight: 700,
      maxFontSizePx: 16,
      maxBlockHeightPx: 18,
      widthPx: 24,
      gapPx: 3,
      insetBlockPx: 4,
      opticalOffsetXEm: 0,
    },
  },
};
