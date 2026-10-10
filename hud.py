"""The heads-up display, drawn in pixels over the 320x200 scene. Independent of Tk.

Each piece is a small Pix plus the texts it shows and the native regions a
click can hit, so the screen can cache pieces and tests can read them.
"""

from dataclasses import dataclass, field
import math

import font
from palette import PLAYER_INK
from dungeon import EFFECT_TEXT, EXIT_HITS, LIVES, PENALTIES, ROOMS, format_seed
from pixels import Pix
from room_art import H, W
from scene import COMPASS, sector_of

TEXT, MUTED, DIM, PANEL, EDGE, GOLD, ALERT, ECO = 10, 8, 5, 1, 4, 16, 25, 28
KIND_INK = {"combat": 28, "elite": 15, "treasure": 16, "mimic": 14, "trap": 24, "sanctuary": 21,
            "empty": 7, "exit": 25, "entrance": 27, "unknown": DIM}
SECTOR_NAMES = {"shallow": "RASO", "middle": "MEIO", "deep": "FUNDO"}
TIER_NAMES = {"easy": "FÁCIL", "medium": "MÉDIA", "hard": "DIFÍCIL"}
POWER_NAMES = {"ward": "ESCUDO", "hex": "MALDIÇÃO", "swap": "TROCA"}
MAP_SIZE = (64, 40)
MAP_AT = (W - MAP_SIZE[0] - 2, 2)
TAB_CENTRE = 186          # between the Turn badge and the minimap, clear of the Guardian
BOX_WIDTH = 312
MAX_QUESTION_LINES = 4
ACTIONS = ("REVANCHE · MESMA SEED", "NOVA SEED", "MENU")
PAUSE_ACTIONS = ("CONTINUAR", "SAIR PARA O MENU")


@dataclass
class Piece:
    pix: Pix
    x: int
    y: int
    texts: list = field(default_factory=list)
    regions: list = field(default_factory=list)   # (action, (x0, y0, x1, y1)) in native pixels


def hearts(player):
    return "♥" * player.lives + "♡" * (LIVES - player.lives)


def panel(w, h, border=EDGE, fill=PANEL):
    p = Pix(w, h, fill)
    for x in range(w):
        p.set(x, 0, border)
        p.set(x, h - 1, border)
    for y in range(h):
        p.set(0, y, border)
        p.set(w - 1, y, border)
    return p


def text_panel(lines, x, y, width=None, border=EDGE, centre=False):
    """A bordered panel holding (text, ink) lines."""
    width = width or max(font.measure(text) for text, _ in lines) + 8
    p = panel(width, len(lines) * font.LINE + 3, border)
    for i, (text, ink) in enumerate(lines):
        left = (width - font.measure(text)) // 2 if centre else 4
        font.draw(p, left, 1 + i * font.LINE, text, ink, shadow=0)
    return Piece(p, x, y, [text for text, _ in lines])


def badge(game):
    """Top-left, one line: whose Turn it is and where they stand; the Map shows which way they look."""
    room = game.current
    if game.status == "playing":
        text, ink = f"J{game.player + 1} · {ROOMS[room.kind][0].upper()} · {SECTOR_NAMES[sector_of(game.dungeon, room)]}", PLAYER_INK[game.player]
    else:
        text, ink = f"J{game.winner + 1} VENCEU", GOLD
    return text_panel([(text, ink)], 2, 2, border=ink)


def minimap(game, facing=0):
    """Top-right: the active player's Map, which way they look, rivals' positions and the Seed.

    Returns the piece plus each revealed room's native centre, the corridors
    drawn, the rivals shown, each room's apparent kind and the cell size,
    so clicks and tests can use them.
    """
    me = game.active
    rivals = [(i, p.position) for i, p in enumerate(game.players) if i != game.player]
    keys = me.revealed | {key for _, key in rivals}
    xs, ys = [k[0] for k in keys], [k[1] for k in keys]
    mw, mh = MAP_SIZE
    cell = max(3, min(12, (mw - 4) // (max(xs) - min(xs) + 1), (mh - 4) // (max(ys) - min(ys) + 1)))
    ox = (mw - cell * (max(xs) - min(xs) + 1)) // 2 - min(xs) * cell
    oy = (mh - cell * (max(ys) - min(ys) + 1)) // 2 - min(ys) * cell
    p = panel(mw, mh + font.LINE + 1)
    # Each room is a square one pixel inside its cell; its centre anchors corridors and clicks.
    squares = {key: (ox + key[0] * cell + 1, oy + key[1] * cell + 1,
                     ox + key[0] * cell + cell - 2, oy + key[1] * cell + cell - 2) for key in keys}
    centres = {key: ((x0 + x1) // 2, (y0 + y1) // 2) for key, (x0, y0, x1, y1) in squares.items()}
    corridors = set()
    for key in me.revealed:
        for other in game.dungeon.connections[key]:
            if other in me.revealed and key < other and (key in me.visited or other in me.visited):
                corridors.add((key, other))
                p.line(*centres[key], *centres[other], DIM)
    kinds = {}
    for key in me.revealed:
        kind = kinds[key] = game.appearance(game.dungeon.rooms[key])
        cx, cy = centres[key]
        x0, y0, x1, y1 = squares[key]
        ink = PLAYER_INK[game.player] if key == me.position else KIND_INK["trap" if key in me.armed else kind]
        if key == me.position or key in me.visited:
            p.rect(x0, y0, x1, y1, ink)
            if key == me.position:          # a needle from the centre towards where the camera looks
                dx, dy = COMPASS[facing][2]
                p.line(cx, cy, cx + dx * (cell // 2 - 1), cy + dy * (cell // 2 - 1), TEXT)
        else:
            for x in range(x0, x1 + 1):        # silhouettes: a dotted outline
                for y in range(y0, y1 + 1):
                    if (x in (x0, x1) or y in (y0, y1)) and (x + y) % 2 == 0:
                        p.set(x, y, ink)
    for i, key in rivals:
        x0, y0, x1, y1 = squares[key]           # each rival takes its own corner of the room
        x, y = (x0, x1 - 1)[i % 2], (y0, y1 - 1)[i // 2]
        p.rect(x, y, x + 1, y + 1, PLAYER_INK[i])
    seed = format_seed(game.seed)
    font.draw(p, (mw - font.measure(seed)) // 2, mh - 1, seed, MUTED)
    x, y = MAP_AT
    piece = Piece(p, x, y, [seed])
    centres = {k: (x + c[0], y + c[1]) for k, c in centres.items() if k in me.revealed}
    return piece, centres, corridors, rivals, kinds, cell


def cards(game, can_retreat):
    """Bottom: one slim card per player; the active one is marked "→", lit in its colour, and holds the actions."""
    n = len(game.players)
    active = game.player if game.status == "playing" else None

    def title(i, short=False):
        player = game.players[i]
        tag = "★" if i == game.winner else "⏸" if player.skip_next else "◆" if player.held and i != active else ""
        depth = "" if short else f" ↓{game.dungeon.rooms[player.position].depth}"
        core = f" X{player.exit_hits}/{EXIT_HITS}" if player.exit_hits and not short else ""
        return f"{'→ ' if i == active else ''}J{i + 1} {hearts(player)}{depth}{core} {tag}".rstrip()

    chips = []                                  # (text, ink, action) on the active card's second line
    if active is not None:
        held = game.players[active].held
        if can_retreat:
            chips.append(("↶ RECUAR", TEXT, ("retreat",)))
        if held:
            chips.append(("◆ " + POWER_NAMES[held], GOLD, None))
        if held in ("hex", "swap"):
            chips += [(f"J{t + 1}", PLAYER_INK[t], ("buff", t)) for t in range(n) if t != active]
    row = sum(font.measure(text) for text, _, _ in chips) + 4 * max(0, len(chips) - 1)
    titles = [title(i) for i in range(n)]

    def widths():
        return [max(font.measure(t), row if i == active else 0) + 8 for i, t in enumerate(titles)]
    if sum(widths()) + 3 * (n - 1) > W - 4:      # crowded: rivals keep only their lives and tag
        titles = [t if i == active else title(i, short=True) for i, t in enumerate(titles)]
    sizes = widths()
    height = font.LINE + 3
    tall = height + (font.LINE if chips else 0)
    p = Pix(W, tall)
    y = H - tall
    piece = Piece(p, 0, y)
    left = (W - sum(sizes) - 3 * (n - 1)) // 2
    for i, w in enumerate(sizes):
        lit = i == active
        h = tall if lit else height
        card = panel(w, h, PLAYER_INK[i] if lit else EDGE)
        font.draw(card, 4, 1, titles[i], PLAYER_INK[i], shadow=0)
        lines = [titles[i]]
        if lit and chips:
            x = 4
            for text, ink, action in chips:
                width = font.draw(card, x, 1 + font.LINE, text, ink, shadow=0)
                if action:
                    top = y + tall - h + 1 + font.LINE
                    piece.regions.append((action, (left + x - 1, top, left + x + width, top + font.HEIGHT)))
                x += width + 4
            lines.append(" ".join(text for text, _, _ in chips))
        p.blit(card, left, tall - h)
        piece.texts.append(lines)
        left += w + 3
    return piece


def spoken_lines(game):
    """What the Guardian says, wrapped for the box: ECO's Taunt lines, then the Question's."""
    question = font.wrap(game.question["question"], BOX_WIDTH - 8)
    if len(question) > MAX_QUESTION_LINES:     # never let the box climb over the top panels
        question = question[:MAX_QUESTION_LINES - 1] + [question[MAX_QUESTION_LINES - 1][:-2] + "…"]
    return font.wrap(game.taunt, BOX_WIDTH - 8), question


def question_lines(game, typed, blink, shown=None):
    """The answer box's lines while a Guardian speaks and waits for an answer.

    `shown` is the spoken lines cut to what has been revealed so far; the
    answer line only appears once everything has been said.
    """
    seconds = math.ceil(game.question_remaining)
    miss = "ESCUDO ANULA" if game.active.held == "ward" else EFFECT_TEXT[game.actual(PENALTIES[game.question_tier])].upper()
    meta = f"J{game.player + 1} · {TIER_NAMES[game.question_tier]} · ERRO: {miss} · {seconds}s"
    if game.current.kind == "exit":
        meta += f" · NÚCLEO {game.active.exit_hits}/{EXIT_HITS}"
    ink = ALERT if seconds <= 5 else PLAYER_INK[game.player]
    taunt, question = spoken_lines(game)
    spoken = taunt + question
    revealed = spoken if shown is None else shown
    lines = [(meta, ink)] + [(line, ECO if i < len(taunt) else TEXT) for i, line in enumerate(revealed)]
    answer = f"> {typed}{'_' if blink else ' '}" if revealed == spoken else ""
    return lines + [(answer, PLAYER_INK[game.player])]


def message_lines(message, ink):
    """A short note above the cards: at most two lines."""
    return [(line, ink) for line in font.wrap(message, BOX_WIDTH - 8)[:2]]


def answer_box(lines, bottom, border, width=BOX_WIDTH):
    """Centred above `bottom`; without a width it fits its text."""
    piece = text_panel(lines, 0, 0, width, border)
    piece.x, piece.y = (W - piece.pix.w) // 2, bottom - piece.pix.h
    return piece


def behind_tab(label, hovered):
    """The door behind the player, as a tab at the top of the screen."""
    piece = text_panel([(label, TEXT if hovered else MUTED)], 0, 2, border=TEXT if hovered else EDGE)
    piece.x = TAB_CENTRE - piece.pix.w // 2
    return piece


def edges():
    """Arrows on the left and right edges that turn the camera."""
    pieces = []
    for label, turn in (("←", -1), ("→", 1)):
        piece = text_panel([(label, TEXT)], 0, 92)
        x = piece.x = 1 if turn < 0 else W - piece.pix.w - 1
        piece.regions.append((("look", turn), (x, 92, x + piece.pix.w - 1, 92 + piece.pix.h - 1)))
        pieces.append(piece)
    return pieces


def mute_toggle(muted, y):
    """Under the minimap: whether sound is on; a click toggles it."""
    piece = text_panel([("SOM ○" if muted else "SOM ●", MUTED if muted else TEXT)], 0, y)
    x = piece.x = W - piece.pix.w - 2
    piece.regions.append((("mute",), (x, y, x + piece.pix.w - 1, y + piece.pix.h - 1)))
    return piece


def duration(seconds):
    """A time as M:SS."""
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def results(game, rank, selected):
    """The centred results panel: who escaped and how fast, a new Record, each player, then the actions.

    Its regions are (("action", i), rect) for each of ACTIONS; `selected` is highlighted.
    """
    winner = game.winner
    lines = [("MASMORRA CONQUISTADA", GOLD), (f"JOGADOR {winner + 1} ESCAPOU", PLAYER_INK[winner]),
             (f"{game.name.upper()} · SEED {format_seed(game.seed)} · {duration(game.elapsed)}", TEXT)]
    if rank:
        lines.append((f"★ NOVO RECORDE · #{rank}", GOLD))
    lines += [("Compartilhe a seed para desafiar alguém.", MUTED), ("", TEXT)]
    for i, player in enumerate(game.players):
        rooms = len(player.visited)
        lines.append((f"J{i + 1} {hearts(player)} · {rooms} {'SALA' if rooms == 1 else 'SALAS'} · "
                      f"NÚCLEO {player.exit_hits}/{EXIT_HITS}", PLAYER_INK[i] if i == winner else MUTED))
    chips = [text_panel([(label, TEXT if i == selected else MUTED)], 0, 0, border=GOLD if i == selected else EDGE)
             for i, label in enumerate(ACTIONS)]
    row = sum(chip.pix.w for chip in chips) + 4 * (len(chips) - 1)
    width = max(row, *(font.measure(text) for text, _ in lines)) + 12
    top = len(lines) * font.LINE + 6
    p = panel(width, top + chips[0].pix.h + 5, GOLD)
    for i, (text, ink) in enumerate(lines):
        font.draw(p, (width - font.measure(text)) // 2, 2 + i * font.LINE, text, ink, shadow=0)
    piece = Piece(p, (W - width) // 2, (H - p.h) // 2, [text for text, _ in lines] + list(ACTIONS))
    x = (width - row) // 2
    for i, chip in enumerate(chips):
        p.blit(chip.pix, x, top)
        piece.regions.append((("action", i), (piece.x + x, piece.y + top,
                                              piece.x + x + chip.pix.w - 1, piece.y + top + chip.pix.h - 1)))
        x += chip.pix.w + 4
    return piece


def pause_panel(game, selected):
    """The pause menu: the Expedition at a glance and two entries; regions are (("pause", i), rect)."""
    info = f"{game.name.upper()} · SEED {format_seed(game.seed)} · {duration(game.elapsed)}"
    width = max(font.measure(info), *(font.measure(a) for a in PAUSE_ACTIONS)) + 24
    p = panel(width, (3 + len(PAUSE_ACTIONS)) * font.LINE + 6, GOLD)
    piece = Piece(p, (W - width) // 2, 0)
    piece.y = (H - p.h) // 2
    rows = [("PAUSA", GOLD), (info, MUTED), ("", TEXT)] + [(a, GOLD if i == selected else TEXT) for i, a in enumerate(PAUSE_ACTIONS)]
    for i, (text, ink) in enumerate(rows):
        y = 3 + i * font.LINE
        choice = i - 3
        if choice == selected:
            p.rect(2, y - 1, width - 3, y + font.LINE - 2, EDGE)
        font.draw(p, (width - font.measure(text)) // 2, y, text, ink, shadow=0)
        if choice >= 0:
            piece.regions.append((("pause", choice), (piece.x + 2, piece.y + y - 1, piece.x + width - 3, piece.y + y + font.LINE - 2)))
        piece.texts.append(text)
    return piece


def banner(lines, y, border):
    piece = text_panel(lines, 0, y, border=border, centre=True)
    piece.x = (W - piece.pix.w) // 2
    return piece
