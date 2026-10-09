"""What the room scene shows to the active player, independent of Tk."""

from dataclasses import dataclass
import random

from dungeon import GUARDED
from props import GRAFFITI, PROP_AT, SLOTS

COMPASS = (("N", "NORTE", (0, -1)), ("L", "LESTE", (1, 0)),
           ("S", "SUL", (0, 1)), ("O", "OESTE", (-1, 0)))
SECTOR_NAMES = ("shallow", "middle", "deep")
TUBE_SPARKS = (216, 12)       # where the broken fluorescent tube hangs


def relative_portals(facing):
    """Compass entries seen as left, ahead, right and behind for a facing."""
    return [COMPASS[(facing + offset) % 4] for offset in (-1, 0, 1, 2)]


def portal_targets(game, facing):
    """For each portal, the index of the matching exit, or None for a wall."""
    exits = game.exits()
    x, y = game.current.key
    return [next((i for i, room in enumerate(exits) if room.key == (x + dx, y + dy)), None)
            for _, _, (dx, dy) in relative_portals(facing)]


def sector_of(dungeon, room):
    """Thirds of the Exit's Depth: shallow near the Entrance, deep by the Exit."""
    return SECTOR_NAMES[min(2, room.depth * 3 // max(1, dungeon.rooms[dungeon.exit_key].depth))]


@dataclass(frozen=True)
class Door:
    portal: int        # 0 left, 1 ahead, 2 right, 3 behind
    exit: int          # index into the Expedition's exits()
    locked: bool


@dataclass(frozen=True)
class Scene:
    seed: int
    room_key: tuple
    kind: str
    sector: str
    facing: int
    doors: tuple
    guardian: str = None   # "dormant", "listening", "cleared", or None without a Guardian
    elite: bool = False
    prop: tuple = None     # (name, state) of the Room kind's prop, as this player knows it
    decor: tuple = ()      # (name, variant, x, y) decorations, the same for every player
    flicker: bool = False  # a broken tube that stutters
    emitters: tuple = ()   # (particle, x, y) sources of ambient particles


def room_prop(game, room):
    """The kind's prop in the state the active player has seen it."""
    me = game.active
    seen = room.key in me.visited      # a Swap can leave someone in a room they never entered
    kind = room.kind
    if kind == "treasure":
        return ("container", "open" if seen else "closed")
    if kind == "mimic":
        return ("mimic", "revealed" if seen else "closed")
    if kind == "trap":
        return ("trap", "spent" if seen else "armed")
    if kind == "sanctuary":
        event = game.event
        healing = bool(event and event["effect"] == "heal" and event["player"] == game.player + 1)
        return ("pod", "healing" if healing else "idle")
    if kind == "empty":
        return ("debris", random.Random(f"debris:{game.seed}:{room.key}").randrange(2))
    if kind == "entrance":
        return ("elevator", None)
    if kind == "exit":
        return ("gate", me.exit_hits)
    return None


def decorations(seed, room_key):
    """Seeded decorations for a room: screens, graffiti, cables, vents and a flickering tube."""
    rng = random.Random(f"decor:{seed}:{room_key}")
    slots = ["left", "right"]
    rng.shuffle(slots)
    decor, emitters = [], [("dust", 0, 0)]
    if rng.random() < .5:
        decor.append(("screen", "eye", *SLOTS[slots.pop()]))
    if rng.random() < .45:
        decor.append(("graffiti", rng.randrange(len(GRAFFITI)), *SLOTS[slots.pop()]))
    if rng.random() < .5:
        x = rng.choice((62, 210))
        decor.append(("cables", rng.randrange(4), x, 0))
        if rng.random() < .6:
            emitters.append(("sparks", x + 21, 50))
    if rng.random() < .35:
        x = rng.choice((36, 250))
        decor.append(("vent", 0, x, 178))
        emitters.append(("steam", x + 17, 178))
    flicker = rng.random() < .4
    if flicker:
        emitters.append(("sparks", *TUBE_SPARKS))
    return tuple(decor), flicker, tuple(emitters)


def scene_for(game, facing):
    room = game.current
    locked = game.status != "playing" or game.question is not None or not game.can_leave()
    doors = tuple(Door(portal, exit, locked)
                  for portal, exit in enumerate(portal_targets(game, facing)) if exit is not None)
    guardian = None
    if room.kind in GUARDED:
        guardian = ("cleared" if game.has_cleared(room) else
                    "listening" if game.question is not None else "dormant")
    prop = room_prop(game, room)
    if prop and prop[0] == "gate" and any(door.portal == 1 for door in doors):
        prop = None            # the gate is on the back wall; a door there hides it
    decor, flicker, emitters = decorations(game.seed, room.key)
    if prop == ("pod", "healing"):
        x, y = PROP_AT["pod"]
        emitters += (("bubbles", x + 23, y + 40),)
    return Scene(game.seed, room.key, room.kind, sector_of(game.dungeon, room), facing, doors, guardian,
                 room.kind == "elite", prop, decor, flicker, emitters)
