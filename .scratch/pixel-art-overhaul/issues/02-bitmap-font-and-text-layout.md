# 02: Bitmap font and text layout

**What to build:** A bitmap font drawn as character grids, about 6×10 per glyph, covering:
- printable ASCII;
- the Portuguese accented letters (á à â ã é ê í ó ô õ ú ç, upper and lower case);
- the symbols the HUD uses: ♥ ♡ ◆ · → ← ↑ ↓ and ×.

A Tk-free layout helper renders a string into the pixel canvas in a given colour, measures it, and wraps text to a pixel width. Long English questions stay legible. This is a prefactor for the HUD, dialogue, menu and results screen.

**Blocked by:** None (can start immediately).

**Status:** done

- [x] Every character in the three question files and in every on-screen Portuguese string has a glyph
- [x] Measuring and wrapping keep every line within the given pixel width; words longer than the width are split
- [x] Text renders into the pixel canvas in any palette colour, with an optional 1-pixel shadow
- [x] An unknown character renders as a visible placeholder instead of failing
- [x] Covered by Tk-free tests
