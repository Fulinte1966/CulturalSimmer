export const SIX_CHARACTER_TITLE_COUNT = 6;

export interface BookTitleLayout {
  characters: string[];
  fillsSixCharacterWidth: boolean;
}

/**
 * Mark titles that need to be distributed across a six-character measure.
 * Each view owns the actual width because the homepage uses square glyph
 * advances while the detail page uses a 0.75em compact display face.
 */
export function getBookTitleLayout(title: string): BookTitleLayout {
  const characters = Array.from(title);
  return {
    characters,
    fillsSixCharacterWidth:
      characters.length > 0 && characters.length < SIX_CHARACTER_TITLE_COUNT,
  };
}
