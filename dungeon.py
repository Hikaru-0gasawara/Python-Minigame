"""Dungeon rules, independent of Tk: a competitive race through one Dungeon."""

from dataclasses import dataclass, field
import random
import time

from dungeon_map import CARDINAL_DIRECTIONS, generate_layout
from questions import TIERS, QuestionBank, is_correct


EASY, MEDIUM, HARD, CAMPAIGN = 1, 2, 3, 4
# Difficulty: on-screen name, Rooms, seconds per Question, % of easy/medium/hard Questions.
MODES = {
    EASY: ("Aventureiro", 15, 30, (70, 25, 5)),
    MEDIUM: ("Guerreiro", 22, 22, (40, 45, 15)),
    HARD: ("Pesadelo", 30, 15, (15, 40, 45)),
    CAMPAIGN: ("Campanha", 30, 30, (85, 12, 3)),
}
SEED_SPACE = 16 ** 8
EXIT_HITS = 3
LIVES = 3
# A missed easy Question hurts most: the penalty shrinks as the Tier rises.
PENALTIES = {"easy": "life", "medium": "skip", "hard": "retreat"}
BUFFS = ("haste", "insight", "ward", "hex", "swap")
HELD = ("ward", "hex", "swap")  # Kept until used; a new one replaces the old.
DEBUFFS = ("retreat", "skip", "life")
EFFECT_TEXT = {"life": "−1 vida", "entrance": "sem vidas, de volta à entrada",
               "skip": "perde a próxima vez", "retreat": "recua uma sala",
               "heal": "+1 vida", "haste": "pressa: mais um movimento",
               "insight": "visão: salas a até 2 passos reveladas",
               "ward": "escudo guardado", "hex": "maldição guardada", "swap": "troca guardada",
               "warded": "o escudo anulou a penalidade"}
GUARDED = {"combat", "elite", "exit"}
# Room kind: on-screen name, hint, colour, generation weight.
ROOMS = {
    "combat": ("Guardião", "Responda para passar", "#24e5dd", 45),
    "elite": ("Elite", "Pergunta difícil · prêmio", "#ff9a5c", 10),
    "treasure": ("Tesouro", "Um baú espera", "#f3c66b", 12),
    "mimic": ("Mímico", "O baú mordeu!", "#d9825b", 5),
    "trap": ("Armadilha", "Já disparada", "#c4a0ff", 10),
    "sanctuary": ("Santuário", "+1 vida a cada visita", "#86e4b4", 6),
    "empty": ("Sala vazia", "Nada aqui", "#8ea2ad", 12),
    "exit": ("Núcleo", f"{EXIT_HITS} acertos para escapar", "#f57888", 0),
    "entrance": ("Entrada", "Ponto de partida", "#66cde5", 0),
    # What an unvisited Room looks like: only its silhouette.
    "unknown": ("Desconhecida", "O que há além?", "#b4c6cf", 0),
}
PLACED = [kind for kind, (*_, weight) in ROOMS.items() if weight]
# What ECO says through a Guardian before its Question: by Tier, or by the Elite and Exit rooms.
TAUNTS = {
    "easy": ("Mais um. Prove que ainda pensa.", "Uma pergunta simples. Até para você.",
             "Responda, e talvez eu te deixe passar.", "Vejamos se você ainda raciocina."),
    "medium": ("Você hesita. Eu nunca hesito.", "Cada erro seu me ensina algo.",
               "Pense rápido. Eu já pensei por você.", "Outros pararam exatamente aqui."),
    "hard": ("Esta eu guardei para os teimosos.", "Ninguém acertou esta em cem anos.",
             "Errar aqui custa caro. Tente.", "Vou gostar de ver você falhar."),
    "elite": ("Eu sou a parede entre você e a saída.", "Fui feita para quebrar quem chega até aqui.",
              "Acerte, e talvez eu sinta algo parecido com respeito."),
    "exit": ("Três verdades e você sai. Nenhuma mentira.", "Ninguém escapa de mim. Prove o contrário.",
             "Este é o meu núcleo. Fale com cuidado."),
}


@dataclass
class Room:
    x: int
    y: int
    kind: str
    depth: int
    effect: str = None

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
    lives: int = LIVES
    skip_next: bool = False
    extra_moves: int = 0
    held: str = None


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
        if (x, y) in ((0, 0), exit_key):
            kind = "entrance" if (x, y) == (0, 0) else "exit"
        else:
            kind = rng.choices(PLACED, [ROOMS[k][3] for k in PLACED])[0]
        effect = (rng.choice(BUFFS) if kind in ("treasure", "elite") else
                  rng.choice(DEBUFFS) if kind in ("mimic", "trap") else
                  "heal" if kind == "sanctuary" else None)
        rooms[x, y] = Room(x, y, kind, depths[x, y], effect)
    return Dungeon(seed, connections, rooms, exit_key)


class Expedition:
    """Players race through one Dungeon, one move per Turn, in fixed order.

    Every action belongs to the active player, so nobody can act out of turn.
    A Guardian questions each player who enters until that player Clears it;
    a miss costs a Life, the next Turn or a Retreat depending on the Tier.
    The first player to answer the Exit's Guardian three times wins.
    """

    def __init__(self, difficulty=EASY, players=1, seed=None, clock=time.monotonic):
        if difficulty not in MODES or not 1 <= players <= 4:
            raise ValueError("Invalid difficulty or player count")
        self.difficulty = difficulty
        self.name, _rooms, self.question_time, self.tier_weights = MODES[difficulty]
        self.seed = random_seed() if seed is None else seed
        self.dungeon = generate_dungeon(self.seed, difficulty)
        # Questions use their own stream so play never alters the Dungeon.
        self.rng = random.Random(f"questions:{self.seed}")
        self.clock = clock
        self.started, self.won_at = clock(), None
        self.bank = QuestionBank()
        entrance = self.dungeon.entrance_key
        self.players = [Player(entrance, cleared={entrance}) for _ in range(players)]
        for player in self.players:
            self._arrive(player, entrance)
        self.player = 0
        self.question = None
        self.question_tier = None
        self.taunt = None
        self.question_deadline = None
        self.question_duration = 0
        self.status = "playing"
        self.winner = None
        self.event = None  # The last Buff or Debuff, for the screen to announce.

    @property
    def active(self):
        return self.players[self.player]

    @property
    def current(self):
        return self.dungeon.rooms[self.active.position]

    @property
    def elapsed(self):
        """Seconds since the Expedition started, frozen at the winner's escape."""
        return (self.clock() if self.won_at is None else self.won_at) - self.started

    @property
    def question_remaining(self):
        """The Question's full time until its clock starts, then what is left of it."""
        if self.question_deadline is None:
            return self.question_duration
        return max(0, self.question_deadline - self.clock())

    def has_cleared(self, room, player=None):
        return room.key in (player or self.active).cleared

    def appearance(self, room, player=None):
        """The kind a player believes a Room is: Mimics pass for Treasure until entered."""
        if room.key in (player or self.active).visited:
            return room.kind
        return "treasure" if room.kind in ("treasure", "mimic") else "unknown"

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
        if self.active.extra_moves:
            self.active.extra_moves -= 1
            return
        self.player = (self.player + 1) % len(self.players)
        while self.active.skip_next:
            self.active.skip_next = False
            self.player = (self.player + 1) % len(self.players)

    def _send_back(self, player):
        """Retreat without spending a Turn of its own: the penalty already ends it."""
        if player.came_from is not None:
            key, player.came_from = player.came_from, player.position
            self._arrive(player, key)

    def _apply(self, player, effect):
        """Apply a Buff or Debuff and return what actually happened."""
        if effect == "life":
            player.lives -= 1
            if player.lives <= 0:
                # Map and Cleared Rooms survive, so the way back is quick.
                effect, player.lives, player.came_from = "entrance", LIVES, None
                self._arrive(player, self.dungeon.entrance_key)
        elif effect == "skip":
            player.skip_next = True
        elif effect == "retreat":
            self._send_back(player)
        elif effect == "heal":
            player.lives = min(LIVES, player.lives + 1)
        elif effect == "haste":
            player.extra_moves += 1
        elif effect in HELD:
            player.held = effect
        elif effect == "insight":
            ring = {player.position}
            for _ in range(2):
                ring = {n for key in ring for n in self.dungeon.connections[key]}
                player.revealed |= ring
        return effect

    def _effect(self, player, effect):
        effect = self._apply(player, effect)
        self.event = {"player": self.players.index(player) + 1, "effect": effect,
                      "text": EFFECT_TEXT[effect]}

    def _move(self, key):
        """Arrive in a Room; a Guardian not yet Cleared keeps the Turn going."""
        player = self.active
        player.came_from = player.position
        first = key not in player.visited
        self._arrive(player, key)
        room = self.current
        self.event = None
        if room.kind in GUARDED and not self.has_cleared(room):
            self.ask()
            return
        player.cleared.add(key)
        # Chests and traps fire once per player; a Sanctuary heals on every visit.
        if room.kind not in GUARDED and room.effect and (first or room.kind == "sanctuary"):
            self._effect(player, room.effect)
        self._end_turn()

    def can_leave(self):
        # Only a Guardian blocks the way; after a Swap a player may stand anywhere.
        return self.current.kind not in GUARDED or self.has_cleared(self.current)

    def enter(self, door):
        if self.status != "playing" or self.question is not None or not self.can_leave():
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

    def use_buff(self, target):
        """Spend a held Hex or Swap on an opponent; it does not use up the Turn."""
        player = self.active
        if (self.status != "playing" or self.question is not None or player.held not in ("hex", "swap")
                or not isinstance(target, int) or not 0 <= target < len(self.players) or target == self.player):
            return False
        rival = self.players[target]
        if player.held == "hex":
            rival.skip_next = True
            text = f"maldição: J{target+1} perde a próxima vez"
        else:
            player.position, rival.position = rival.position, player.position
            for racer in (player, rival):
                # Visited and Cleared stay as they were; each racer just sees where they now stand.
                racer.came_from = None
                racer.revealed.add(racer.position)
                racer.revealed.update(self.dungeon.connections[racer.position])
            text = f"trocou de lugar com J{target+1}"
        self.ask()  # Before recording the event: asking clears the last one.
        self.event = {"player": self.player + 1, "effect": player.held, "text": text}
        player.held = None
        return True

    def ask(self):
        if (self.status != "playing" or self.question is not None
                or self.current.kind not in GUARDED or self.has_cleared(self.current)):
            return
        self.event = None
        self.question_tier = ("hard" if self.current.kind == "elite"
                              else self.rng.choices(TIERS, self.tier_weights)[0])
        self.question = self.bank.draw(self.question_tier, self.rng)
        kind = self.current.kind
        self.taunt = self.rng.choice(TAUNTS[kind if kind in ("elite", "exit") else self.question_tier])
        self.question_duration = self.question_time
        self.question_deadline = None

    def start_clock(self):
        """Start the Question's time once the screen has shown all of it."""
        if self.question is not None and self.question_deadline is None:
            self.question_deadline = self.clock() + self.question_duration

    def tick(self):
        if (self.status == "playing" and self.question is not None and self.question_deadline is not None
                and self.question_remaining <= 0):
            return self.submit("", expired=True)
        return None

    def submit(self, answer, expired=False):
        if self.status != "playing" or self.question is None:
            return None
        expired = expired or self.question_remaining <= 0
        question, player, room = self.question, self.active, self.current
        correct = not expired and is_correct(question, answer)
        penalty = None
        if not correct:
            if player.held == "ward":
                player.held, penalty = None, "warded"
            else:
                penalty = self._apply(player, PENALTIES[self.question_tier])
            reason = "Tempo da pergunta esgotado" if expired else "Resposta incorreta"
            message = f"{reason}. Resposta: {question['answer']} · {EFFECT_TEXT[penalty]}"
        elif room.kind == "exit":
            player.exit_hits += 1
            message = f"Núcleo {player.exit_hits}/{EXIT_HITS}"
            if player.exit_hits >= EXIT_HITS:
                player.cleared.add(room.key)
                self.status, self.winner, self.won_at = "won", self.player, self.clock()
                message = "Escapou da masmorra!"
        else:
            player.cleared.add(room.key)
            message = "Guardião vencido. Passagem liberada."
            if room.kind == "elite":
                self._effect(player, room.effect)
                message += f" Prêmio: {self.event['text']}."
        result = {"correct": correct, "expired": expired, "message": message,
                  "answer": question["answer"], "player": self.player + 1,
                  "tier": self.question_tier, "penalty": penalty}
        if self.status == "won":
            self.question = None
        else:
            self._end_turn()
        return result
