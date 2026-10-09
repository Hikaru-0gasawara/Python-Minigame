"""The heads-up display, drawn in pixels over the 320x200 scene. Independent of Tk.

Each piece is a small Pix plus the texts it shows and the native regions a
click can hit, so the screen can cache pieces and tests can read them.
"""

from dataclasses import dataclass, field
import math

import font
from dungeon import EFFECT_TEXT, EXIT_HITS, LIVES, PENALTIES, ROOMS, format_seed
from pixels import Pix
from room_art import H, W
from scene import COMPASS, sector_of

PLAYER_INK = (29, 17, 31, 21)           # cyan, amber, violet, green
TEXT, MUTED, DIM, PANEL, EDGE, GOLD, ALERT = 10, 8, 5, 1, 4, 16, 25
KIND_INK = {"combat": 28, "elite": 15, "treasure": 16, "mimic": 14, "trap": 24, "sanctuary": 21,
            "empty": 7, "exit": 25, "entrance": 27, "unknown": DIM}
SECTOR_NAMES = {"shallow": "RASO", "middle": "MEIO", "deep": "FUNDO"}
TIER_NAMES = {"easy": "FÁCIL", "medium": "MÉDIA", "hard": "DIFÍCIL"}
POWER_NAMES = {"ward": "ESCUDO", "hex": "MALDIÇÃO", "swap": "TROCA"}
MAP_AT, MAP_SIZE = (236, 2), (82, 52)
TAB_CENTRE = 186          # between the Turn badge and the minimap, clear of the Guardian
CARDS_TOP = H - 46
BOX_WIDTH = 312
MAX_QUESTION_LINES = 4


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


def badge(game, facing):
    """Top-left: whose Turn it is, where they stand and which way they look."""
    room = game.current
    if game.status == "playing":
        first = (f"J{game.player + 1} · SUA VEZ", PLAYER_INK[game.player])
    else:
        first = (f"J{game.winner + 1} VENCEU", GOLD)
    return text_panel([first,
                       (f"{ROOMS[room.kind][0].upper()} · {SECTOR_NAMES[sector_of(game.dungeon, room)]}", TEXT),
                       (f"OLHANDO {COMPASS[facing][1]}  ESC MENU", MUTED)], 2, 2,
                      border=first[1])


def minimap(game):
    """Top-right: the active player's Map, rivals' positions and the Seed.

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
        ink = PLAYER_INK[game.player] if key == me.position else KIND_INK[kind]
        if key == me.position or key in me.visited:
            p.rect(x0, y0, x1, y1, ink)
            if key == me.position:
                p.set(cx, cy, TEXT)
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
    """Bottom: one card per player; the active one is wider, taller and holds the actions."""
    n = len(game.players)
    active = game.player if game.status == "playing" else None
    wide = 112 if n > 1 else 140
    narrow = min(78, (W - 4 - wide - 3 * (n - 1)) // max(1, n - 1))
    widths = [wide if i == active or n == 1 else narrow for i in range(n)]
    left = (W - sum(widths) - 3 * (n - 1)) // 2
    p = Pix(W, H - CARDS_TOP)
    texts, regions = [], []
    for i, player in enumerate(game.players):
        w, ink = widths[i], PLAYER_INK[i]
        is_active = i == active
        top = 0 if is_active else 14
        card = panel(w, H - CARDS_TOP - top, ink if is_active else EDGE)
        tag = ("· SUA VEZ" if is_active else "★" if i == game.winner else "⏸" if player.skip_next
               else "◆" if player.held else "")
        title = f"J{i + 1} {hearts(player)} {tag}".rstrip()
        status = f"↓{game.dungeon.rooms[player.position].depth}  X {player.exit_hits}/{EXIT_HITS}"
        font.draw(card, 4, 1, title, ink, shadow=0)
        font.draw(card, 4, 1 + font.LINE, status, TEXT if is_active else MUTED, shadow=0)
        lines = [title, status]
        if is_active:
            row = 1 + 2 * font.LINE
            x = 4

            def chip(text, ink, action=None):
                nonlocal x
                width = font.draw(card, x, row, text, ink, shadow=0)
                if action:
                    regions.append((action, (left + x - 1, CARDS_TOP + row, left + x + width, CARDS_TOP + row + font.HEIGHT)))
                x += width + 4
            if can_retreat:
                chip("↶ RECUAR", TEXT, ("retreat",))
            if player.held == "ward":
                chip("◆ " + POWER_NAMES["ward"], GOLD)
            elif player.held:
                chip("◆", GOLD)
                for t in range(n):
                    if t != i:
                        chip(f"J{t + 1}", PLAYER_INK[t], ("buff", t))
            lines.append(f"{'↶ RECUAR ' if can_retreat else ''}"
                         f"{'◆ ' + POWER_NAMES[player.held] if player.held else ''}".strip())
        p.blit(card, left, top)
        texts.append(lines)
        left += w + 3
    return Piece(p, 0, CARDS_TOP, texts, regions)


def question_lines(game, typed, blink):
    """The answer box's lines while a Guardian waits for an answer."""
    seconds = math.ceil(game.question_remaining)
    miss = "ESCUDO ANULA" if game.active.held == "ward" else EFFECT_TEXT[PENALTIES[game.question_tier]].upper()
    meta = f"J{game.player + 1} · {TIER_NAMES[game.question_tier]} · ERRO: {miss} · {seconds}s"
    if game.current.kind == "exit":
        meta += f" · NÚCLEO {game.active.exit_hits}/{EXIT_HITS}"
    ink = ALERT if seconds <= 5 else PLAYER_INK[game.player]
    question = font.wrap(game.question["question"], BOX_WIDTH - 8)
    if len(question) > MAX_QUESTION_LINES:     # never let the box climb over the top panels
        question = question[:MAX_QUESTION_LINES - 1] + [question[MAX_QUESTION_LINES - 1][:-2] + "…"]
    lines = [(meta, ink)] + [(line, TEXT) for line in question]
    return lines + [(f"> {typed}{'_' if blink else ' '}", PLAYER_INK[game.player])]


def message_lines(game, message, ink, can_retreat):
    if game.status != "playing":
        return [(f"Jogador {game.winner + 1} escapou da masmorra!", GOLD)]
    if game.can_leave():
        hint = "ESCOLHA UMA PASSAGEM · ALT+SETAS: MOVER"
    else:
        hint = "O GUARDIÃO AGUARDA" + (" · ALT+R RECUA" if can_retreat else "")
    return [(line, ink) for line in font.wrap(message, BOX_WIDTH - 8)[:2]] + [(hint, MUTED)]


def answer_box(lines, bottom, border):
    piece = text_panel(lines, (W - BOX_WIDTH) // 2, 0, BOX_WIDTH, border)
    piece.y = bottom - piece.pix.h
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


def banner(lines, y, border):
    piece = text_panel(lines, 0, y, border=border, centre=True)
    piece.x = (W - piece.pix.w) // 2
    return piece
