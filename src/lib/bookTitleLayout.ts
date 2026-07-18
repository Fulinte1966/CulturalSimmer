export const SEVEN_CHARACTER_TITLE_COUNT = 7;

export interface BookTitleLayout {
  characters: string[];
  fillsSevenCharacterWidth: boolean;
}

/**
 * Mark titles that need to be distributed across a seven-character measure.
 * Each view owns the actual width because the homepage uses square glyph
 * advances while the detail page uses a 0.75em compact display face.
 */
export function getBookTitleLayout(title: string): BookTitleLayout {
  const characters = Array.from(title);
  return {
    characters,
    fillsSevenCharacterWidth:
      characters.length > 0 && characters.length < SEVEN_CHARACTER_TITLE_COUNT,
  };
}
