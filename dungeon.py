"""Dungeon rules, independent of Tk: a competitive race through one Dungeon."""

from dataclasses import dataclass, field
import random
import time

from dungeon_map import CARDINAL_DIRECTIONS, generate_layout
from questions import TIERS, QuestionBank, is_correct


EASY, MEDIUM, HARD, CAMPAIGN = 1, 2, 3, 4
# Difficulty: on-screen name, Rooms, seconds per Question.
MODES = {
    EASY: ("Aventureiro", 15, 30),
    MEDIUM: ("Guerreiro", 22, 22),
    HARD: ("Pesadelo", 30, 15),
    CAMPAIGN: ("Campanha", 30, 30),
}
SEED_SPACE = 16 ** 8
EXIT_HITS = 3
# Room kind: on-screen name, hint, colour.
ROOMS = {
    "combat": ("Guardião", "Responda para passar", "#24e5dd"),
    "exit": ("Núcleo", f"{EXIT_HITS} acertos para escapar", "#f57888"),
    "entrance": ("Entrada", "Ponto de partida", "#66cde5"),
}


@dataclass
class Room:
    x: int
    y: int
    kind: str
    depth: int

    @property
    def key(self):
        return self.x, self.y


@dataclass
class Dungeon:
    """The generated place: Rooms on an orthogonal grid joined by passages."""

    seed: int
    connections: dict
    rooms: dict
    exit_key: tuple
    entrance_key: tuple = (0, 0)


@dataclass
class Player:
    """Everything one racer knows and has done; nothing here is shared."""

    position: tuple
    came_from: tuple = None
    visited: set = field(default_factory=set)
    revealed: set = field(default_factory=set)
    cleared: set = field(default_factory=set)
    exit_hits: int = 0


def random_seed():
    return random.randrange(SEED_SPACE)


def format_seed(seed):
    text = f"{seed:08X}"
    return f"{text[:4]}-{text[4:]}"


def parse_seed(text):
    """Return the Seed typed by a player, or None when it is not one."""
    digits = text.replace("-", "").replace(" ", "")
    if not 1 <= len(digits) <= 8 or not all(c in "0123456789abcdefABCDEF" for c in digits):
        return None
    return int(digits, 16)


def generate_dungeon(seed, difficulty):
    """The same Seed and Difficulty always produce the same Dungeon."""
    rng = random.Random(seed)
    connections, depths, exit_key = generate_layout(rng, MODES[difficulty][1])
    rooms = {}
    for x, y in connections:
        kind = "entrance" if (x, y) == (0, 0) else "exit" if (x, y) == exit_key else "combat"
        rooms[x, y] = Room(x, y, kind, depths[x, y])
    return Dungeon(seed, connections, rooms, exit_key)


class Expedition:
    """Players race through one Dungeon, one move per Turn, in fixed order.

    Every action belongs to the active player, so nobody can act out of turn.
    A Guardian questions each player who enters until that player Clears it;
    the first player to answer the Exit's Guardian three times wins.
    """

    def __init__(self, difficulty=EASY, players=1, seed=None, clock=time.monotonic):
        if difficulty not in MODES or not 1 <= players <= 4:
            raise ValueError("Invalid difficulty or player count")
        self.difficulty = difficulty
        self.name, _rooms, self.base_question_time = MODES[difficulty]
        self.seed = random_seed() if seed is None else seed
        self.dungeon = generate_dungeon(self.seed, difficulty)
        # Questions use their own stream so play never alters the Dungeon.
        self.rng = random.Random(f"questions:{self.seed}")
        self.clock = clock
        self.bank = QuestionBank()
        entrance = self.dungeon.entrance_key
        self.players = [Player(entrance, cleared={entrance}) for _ in range(players)]
        for player in self.players:
            self._arrive(player, entrance)
        self.player = 0
        self.question = None
        self.question_deadline = 0
        self.question_duration = 0
        self.status = "playing"
        self.winner = None

    @property
    def active(self):
        return self.players[self.player]

    @property
    def current(self):
        return self.dungeon.rooms[self.active.position]

    @property
    def question_remaining(self):
        return max(0, self.question_deadline - self.clock())

    def has_cleared(self, room, player=None):
        return room.key in (player or self.active).cleared

    def exits(self, room=None):
        """Existing doors in compass order, including already visited rooms."""
        x, y = (room or self.current).key
        return [self.dungeon.rooms[x + dx, y + dy] for dx, dy in CARDINAL_DIRECTIONS
                if (x + dx, y + dy) in self.dungeon.connections[x, y]]

    def _arrive(self, player, key):
        player.position = key
        player.visited.add(key)
        player.revealed.add(key)
        player.revealed.update(self.dungeon.connections[key])

    def _end_turn(self):
        self.question = None
        self.player = (self.player + 1) % len(self.players)

    def _move(self, key):
        """Arrive in a Room; a Guardian not yet Cleared keeps the Turn going."""
        player = self.active
        player.came_from = player.position
        self._arrive(player, key)
        if self.has_cleared(self.current):
            self._end_turn()
        else:
            self.ask()

    def enter(self, door):
        if self.status != "playing" or self.question is not None or not self.has_cleared(self.current):
            return False
        exits = self.exits()
        if not isinstance(door, int) or not 0 <= door < len(exits):
            return False
        self._move(exits[door].key)
        return True

    def retreat(self):
        """Go back to the Room the player came from, abandoning any Question."""
        if self.status != "playing" or self.active.came_from is None:
            return False
        self.question = None
        self._move(self.active.came_from)
        return True

    def ask(self):
        if self.status != "playing" or self.question is not None or self.has_cleared(self.current):
            return
        tier = min(2, self.current.depth * 3 // self.dungeon.rooms[self.dungeon.exit_key].depth)
        self.question = self.bank.draw(TIERS[tier if self.difficulty == CAMPAIGN else self.difficulty - 1], self.rng)
        duration = self.base_question_time
        if self.difficulty == CAMPAIGN:
            duration = (30, 22, 15)[tier]
        self.question_duration = duration
        self.question_deadline = self.clock() + duration

    def tick(self):
        if self.status == "playing" and self.question is not None and self.question_remaining <= 0:
            return self.submit("", expired=True)
        return None

    def submit(self, answer, expired=False):
        if self.status != "playing" or self.question is None:
            return None
        expired = expired or self.question_remaining <= 0
        question, player, room = self.question, self.active, self.current
        correct = not expired and is_correct(question, answer)
        if not correct:
            reason = "Tempo da pergunta esgotado" if expired else "Resposta incorreta"
            message = f"{reason}. Resposta: {question['answer']}"
        elif room.kind == "exit":
            player.exit_hits += 1
            message = f"Núcleo {player.exit_hits}/{EXIT_HITS}"
            if player.exit_hits >= EXIT_HITS:
                player.cleared.add(room.key)
                self.status, self.winner = "won", self.player
                message = "Escapou da masmorra!"
        else:
            player.cleared.add(room.key)
            message = "Guardião vencido. Passagem liberada."
        result = {"correct": correct, "expired": expired, "message": message,
                  "answer": question["answer"], "player": self.player + 1}
        if self.status == "won":
            self.question = None
        else:
            self._end_turn()
        return result
