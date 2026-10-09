"""What the room scene shows to the active player, independent of Tk."""

from dataclasses import dataclass

from dungeon import GUARDED

COMPASS = (("N", "NORTE", (0, -1)), ("L", "LESTE", (1, 0)),
           ("S", "SUL", (0, 1)), ("O", "OESTE", (-1, 0)))
SECTOR_NAMES = ("shallow", "middle", "deep")


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


def scene_for(game, facing):
    room = game.current
    locked = game.status != "playing" or game.question is not None or not game.can_leave()
    doors = tuple(Door(portal, exit, locked)
                  for portal, exit in enumerate(portal_targets(game, facing)) if exit is not None)
    guardian = None
    if room.kind in GUARDED:
        guardian = ("cleared" if game.has_cleared(room) else
                    "listening" if game.question is not None else "dormant")
    return Scene(game.seed, room.key, room.kind, sector_of(game.dungeon, room), facing, doors, guardian)
