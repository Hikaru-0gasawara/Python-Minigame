"""A proportional bitmap font for the pixel-art screens, drawn as character grids.

Every glyph sits in a 12-row cell. Capitals are 7 rows tall below a 2-row band
for their accents and a blank row; lowercase letters are 5 rows tall, with
their accents two rows higher so a blank row always separates mark and letter;
descenders take the last 2 rows. Accented letters are composed from a base
letter and an accent mark, so any Latin accent works.
"""

import unicodedata

HEIGHT = 12        # cell height in pixels
LINE = 13          # vertical advance between lines
TOP = 3            # first cell row of a base glyph; rows above hold capital accents

# Rows of each base glyph from the top of its 9-row body; '#' is ink. Missing rows are blank.
_BASE = {
    " ": "..",
    "!": "# # # # # . #",
    '"': "#.# #.#",
    "#": ".#.#. .#.#. ##### .#.#. ##### .#.#. .#.#.",
    "$": "..#.. .#### #.#.. .###. ..#.# ####. ..#..",
    "%": "##..# ##..# ...#. ..#.. .#... #..## #..##",
    "&": ".##.. #..#. #.#.. .#... #.#.# #..#. .##.#",
    "'": "# #",
    "(": "..# .#. #.. #.. #.. .#. ..#",
    ")": "#.. .#. ..# ..# ..# .#. #..",
    "*": "..... ..#.. #.#.# .###. #.#.# ..#..",
    "+": "..... ..... ..#.. ..#.. ##### ..#.. ..#..",
    ",": ".. .. .. .. .. .# .# #.",
    "-": ".... .... .... .... ####",
    ".": ". . . . . . #",
    "/": "....# ...#. ...#. ..#.. .#... .#... #....",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
    "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    "2": ".###. #...# ....# ...#. ..#.. .#... #####",
    "3": ".###. #...# ....# ..##. ....# #...# .###.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": "..##. .#... #.... ####. #...# #...# .###.",
    "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ...#. .##..",
    ":": ". . . # . . #",
    ";": ".. .. .. .# .. .. .# #.",
    "<": "... ... ..# .#. #.. .#. ..#",
    "=": ".... .... .... #### .... ####",
    ">": "... ... #.. .#. ..# .#. #..",
    "?": ".###. #...# ....# ...#. ..#.. ..... ..#..",
    "@": ".###. #...# #.### #.#.# #.### #.... .###.",
    "A": ".###. #...# #...# ##### #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "####. #...# #...# #...# #...# #...# ####.",
    "E": "##### #.... #.... ####. #.... #.... #####",
    "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .####",
    "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": "### .#. .#. .#. .#. .#. ###",
    "J": "..### ...#. ...#. ...#. ...#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    "N": "#...# ##..# #.#.# #..## #...# #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".###. #...# #.... .###. ....# #...# .###.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #.#.# #.#.# ##.## #...#",
    "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "[": "## #. #. #. #. #. ##",
    "\\": "#.... .#... .#... ..#.. ...#. ...#. ....#",
    "]": "## .# .# .# .# .# ##",
    "^": "..#.. .#.#. #...#",
    "_": "..... ..... ..... ..... ..... ..... ..... #####",
    "`": "#. .#",
    "a": "..... ..... .###. ....# .#### #...# .####",
    "b": "#.... #.... ####. #...# #...# #...# ####.",
    "c": "..... ..... .###. #.... #.... #.... .###.",
    "d": "....# ....# .#### #...# #...# #...# .####",
    "e": "..... ..... .###. #...# ##### #.... .###.",
    "f": "..## .#.. ###. .#.. .#.. .#.. .#..",
    "g": "..... ..... .#### #...# #...# #...# .#### ....# .###.",
    "h": "#.... #.... ####. #...# #...# #...# #...#",
    "i": "# . # # # # #",
    "ı": ". . # # # # #",                                 # dotless i, for í, ì, î
    "j": "..# ... ..# ..# ..# ..# ..# ..# ##.",
    "ȷ": "... ... ..# ..# ..# ..# ..# ..# ##.",           # dotless j
    "k": "#... #... #..# #.#. ##.. #.#. #..#",
    "l": "#. #. #. #. #. #. .#",
    "m": "..... ..... ##.#. #.#.# #.#.# #.#.# #.#.#",
    "n": "..... ..... ####. #...# #...# #...# #...#",
    "o": "..... ..... .###. #...# #...# #...# .###.",
    "p": "..... ..... ####. #...# #...# #...# ####. #.... #....",
    "q": "..... ..... .#### #...# #...# #...# .#### ....# ....#",
    "r": ".... .... #.## ##.. #... #... #...",
    "s": "..... ..... .#### #.... .###. ....# ####.",
    "t": ".#.. .#.. ###. .#.. .#.. .#.. ..##",
    "u": "..... ..... #...# #...# #...# #...# .####",
    "v": "..... ..... #...# #...# #...# .#.#. ..#..",
    "w": "..... ..... #...# #...# #.#.# #.#.# .#.#.",
    "x": "..... ..... #...# .#.#. ..#.. .#.#. #...#",
    "y": "..... ..... #...# #...# #...# #...# .#### ....# .###.",
    "z": "..... ..... ##### ...#. ..#.. .#... #####",
    "{": ".## .#. .#. #.. .#. .#. .##",
    "|": "# # # # # # # # #",
    "}": "##. .#. .#. ..# .#. .#. ##.",
    "~": "..... ..... ..... .##.# #..#.",
    # Symbols used by the HUD and the question bank.
    "·": ".. .. .. ## ##",
    "•": "... ... ... .#. ### .#.",
    "×": "..... ..... #...# .#.#. ..#.. .#.#. #...#",
    "÷": "..... ..... ..#.. ..... ##### ..... ..#..",
    "…": "..... ..... ..... ..... ..... ..... #.#.#",
    "←": "..... ..... ..#.. .#... ##### .#... ..#..",
    "→": "..... ..... ..#.. ...#. ##### ...#. ..#..",
    "↑": "..... ..#.. .###. #.#.# ..#.. ..#.. ..#..",
    "↓": "..... ..#.. ..#.. ..#.. #.#.# .###. ..#..",
    "↵": "..... ..... ....# ....# .#..# ##### .#...",
    "↶": "..... ..... .#... ####. .#..# ....# ..##.",
    "↷": "..... ..... ...#. .#### #..#. #.... .##..",
    "⏸": "..... ##.## ##.## ##.## ##.## ##.##",
    "◆": "..... ..#.. .###. ##### .###. ..#..",
    "◇": "..... ..#.. .#.#. #...# .#.#. ..#..",
    "○": "..... .###. #...# #...# #...# .###.",
    "●": "..... .###. ##### ##### ##### .###.",
    "★": "..#.. ..#.. ##### .###. .#.#. #...#",
    "♥": "..... ##.## ##### ##### .###. ..#..",
    "♡": "..... ##.## #.#.# #...# .#.#. ..#..",
    "✓": "..... ..... ....# ...#. #.#.. .#...",
}
# Accent marks drawn above a letter (2 rows) and the cedilla drawn below it.
_ACCENTS = {
    "́": "..# .#.",        # acute
    "̀": "#.. .#.",        # grave
    "̂": ".#. #.#",        # circumflex
    "̃": ".##.# #..#.",    # tilde
    "̈": "... #.#",        # diaeresis
    "̊": ".#. #.#",        # ring
}
_CEDILLA = ".#. ##."
_DOTLESS = {"i": "ı", "j": "ȷ"}
_ALIASES = {"−": "-", "–": "-", "—": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
            " ": " ", "\t": " "}
_PLACEHOLDER = "##### #...# #...# #...# #...# #...# #####"


def _rows(spec):
    return spec.split(" ")


def _pixels(spec, x0=0, y0=TOP):
    return {(x0 + x, y0 + y) for y, row in enumerate(_rows(spec)) for x, c in enumerate(row) if c == "#"}


def _compose(ch):
    """Build a glyph as (width, pixels) from a base glyph and its accent marks."""
    if ch in _BASE:
        return len(_rows(_BASE[ch])[0]), frozenset(_pixels(_BASE[ch]))
    parts = unicodedata.normalize("NFD", ch)
    base, marks = parts[0], parts[1:]
    if base not in _BASE or not marks or any(m not in _ACCENTS and m != "̧" for m in marks):
        return None
    above = [m for m in marks if m in _ACCENTS]
    base = _DOTLESS.get(base, base) if above else base
    body = _BASE[base]
    width = max([len(_rows(body)[0])] + [len(_rows(_ACCENTS[m])[0]) for m in above]
                + ([3] if "̧" in marks else []))
    pixels = _pixels(body, (width - len(_rows(body)[0])) // 2)
    for mark in above:
        spec = _ACCENTS[mark]
        # Capitals take the band above the cell's body; lowercase use their ascender rows.
        pixels |= _pixels(spec, (width - len(_rows(spec)[0])) // 2, 0 if base.isupper() else TOP - 1)
    if "̧" in marks:
        pixels |= _pixels(_CEDILLA, (width - 3) // 2, TOP + 7)
    return width, frozenset(pixels)


_cache = {}


def glyph(ch):
    """(width, pixels) for a character; unknown characters get a visible box."""
    ch = _ALIASES.get(ch, ch)
    if ch not in _cache:
        _cache[ch] = _compose(ch)
    return _cache[ch] or (5, frozenset(_pixels(_PLACEHOLDER)))


def known(ch):
    ch = _ALIASES.get(ch, ch)
    if ch not in _cache:
        _cache[ch] = _compose(ch)
    return _cache[ch] is not None


def measure(text):
    """Width in pixels of one line: glyph widths plus one pixel between glyphs."""
    return sum(glyph(c)[0] for c in text) + max(0, len(text) - 1)


def wrap(text, width):
    """Greedy word wrap to a pixel width; words wider than a line are split."""
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            while measure(word) > width:
                cut = 1
                while measure(word[:cut + 1]) <= width:
                    cut += 1
                if line:
                    lines.append(line)
                    line = ""
                lines.append(word[:cut])
                word = word[cut:]
            candidate = f"{line} {word}" if line else word
            if measure(candidate) <= width:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw(pix, x, y, text, color, shadow=None):
    """Draw one line with its cell's top-left at (x, y); returns the width drawn."""
    passes = [(1, 1, shadow)] if shadow is not None else []
    for dx, dy, c in passes + [(0, 0, color)]:
        cx = x + dx
        for ch in text:
            w, pixels = glyph(ch)
            for px, py in pixels:
                pix.set(cx + px, y + dy + py, c)
            cx += w + 1
    return measure(text)
