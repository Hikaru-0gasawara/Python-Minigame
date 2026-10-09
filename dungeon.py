"""Dungeon rules, independent of Tk: spatial exploration, trivia and rewards."""

from dataclasses import dataclass
import random
import time

from dungeon_map import CARDINAL_DIRECTIONS, generate_layout
from questions import TIERS, QuestionBank, is_correct


MODES = {
    1: ("Explorador", 9, 240, 30),
    2: ("Aventureiro", 12, 190, 22),
    3: ("Pesadelo", 15, 145, 15),
    4: ("Campanha", 18, 300, 30),
}
ROOMS = {
    "combat": ("Terminal", "Desafio de quiz", "#24e5dd", 1.0),
    "treasure": ("Cache", "Pontos ×1,5", "#f3c66b", 1.5),
    "elite": ("Sobrecarga", "Pontos ×2 · tempo −25%", "#f57888", 2.0),
    "sanctuary": ("Recuperação", "+1 vida ao acertar", "#86e4b4", 1.0),
    "clock": ("Sincronizador", "+12s ao acertar", "#b49aff", 1.0),
    "boss": ("Núcleo", "3 acertos para vencer", "#f57888", 3.0),
    "entrance": ("Entrada", "Escolha sua primeira porta", "#66cde5", 1.0),
}


@dataclass
class Room:
    x: int
    y: int
    kind: str
    depth: int
    cleared: bool = False
    hits: int = 0

    @property
    def key(self):
        return self.x, self.y


class Dungeon:
    """Connected rooms occupy a grid with actual north/east/south/west doors.

    The entire expedition shares a clock and lives. In local cooperative play,
    each submitted answer rotates the active player and scores individually.
    """

    def __init__(self, difficulty=1, players=1, rng=None, clock=time.monotonic):
        if difficulty not in MODES or not 1 <= players <= 4:
            raise ValueError("Invalid difficulty or player count")
        self.difficulty = difficulty
        self.name, size, budget, self.base_question_time = MODES[difficulty]
        self.rng = rng or random.Random()
        self.clock = clock
        self.deadline = clock() + budget
        self.budget = budget
        self.bank = QuestionBank()
        self.room_count = 3 * (size - 1) + 2
        self.connections, depths, self.boss_key = generate_layout(self.rng, self.room_count)
        self.floors = depths[self.boss_key]
        self.rooms = {}
        for x, y in self.connections:
            kind = self.rng.choice(list(ROOMS)[:5])
            if (x, y) == (0, 0):
                kind = "entrance"
            elif (x, y) == self.boss_key:
                kind = "boss"
            self.rooms[x, y] = Room(x, y, kind, depths[x, y], cleared=kind == "entrance")
        self.current = self.rooms[0, 0]
        self.history = []
        self.visited = {self.current.key}
        self.revealed = {self.current.key}
        self.scores = [0] * players
        self.player = 0
        self.combo = 0
        self.best_combo = 0
        self.lives = 5
        self.question = None
        self.question_deadline = 0
        self.question_duration = 0
        self.status = "playing"
        self.finished_remaining = None
        self.reveal()

    @property
    def remaining(self):
        if self.finished_remaining is not None:
            return self.finished_remaining
        return max(0, self.deadline - self.clock())

    def finish(self, status):
        self.finished_remaining = self.remaining
        self.status = status

    @property
    def question_remaining(self):
        return max(0, min(self.remaining, self.question_deadline - self.clock()))

    def exits(self):
        """Existing doors in compass order, including already visited rooms."""
        x, y = self.current.key
        return [self.rooms[x + dx, y + dy] for dx, dy in CARDINAL_DIRECTIONS
                if (x + dx, y + dy) in self.connections[self.current.key]]

    def reveal(self):
        self.revealed.update(room.key for room in self.exits())

    def enter(self, door):
        if self.status != "playing" or self.remaining <= 0 or not self.current.cleared:
            return False
        exits = self.exits()
        if not isinstance(door, int) or not 0 <= door < len(exits):
            return False
        self.history.append(self.current.key)
        self.current = exits[door]
        self.visited.add(self.current.key)
        self.reveal()
        self.ask()
        return True

    def back(self):
        if self.status != "playing" or self.remaining <= 0 or not self.current.cleared or not self.history:
            return False
        self.current = self.rooms[self.history.pop()]
        self.reveal()
        return True

    def ask(self):
        if self.status != "playing" or self.remaining <= 0 or self.current.cleared or self.question is not None:
            return
        tier = min(2, self.current.depth * 3 // self.floors)
        self.question = self.bank.draw(TIERS[tier if self.difficulty == 4 else self.difficulty - 1], self.rng)
        duration = self.base_question_time
        if self.difficulty == 4:
            duration = (30, 22, 15)[tier]
        if self.current.kind == "elite":
            duration *= .75
        self.question_duration = duration
        self.question_deadline = self.clock() + duration

    def tick(self):
        if self.status != "playing":
            return None
        if self.remaining <= 0:
            self.finish("lost")
            self.question = None
            return {"correct": False, "points": 0, "message": "A masmorra se fechou. Tempo esgotado!"}
        if self.question is not None and self.question_remaining <= 0:
            return self.submit("", expired=True)
        return None

    def submit(self, answer, expired=False):
        if self.status != "playing" or self.question is None:
            return None
        if self.remaining <= 0:
            return self.tick()
        expired = expired or self.question_remaining <= 0
        question = self.question
        correct = not expired and is_correct(question, answer)
        points = 0
        if correct:
            self.combo += 1
            self.best_combo = max(self.combo, self.best_combo)
            multiplier = 1 + min(self.combo - 1, 9) * .25
            speed = int(1000 * self.question_remaining / self.question_duration)
            points = int((1000 + speed) * multiplier * ROOMS[self.current.kind][3])
            self.scores[self.player] += points
            self.current.hits += 1
            self.current.cleared = self.current.kind != "boss" or self.current.hits >= 3
            reward = ""
            if self.current.cleared:
                if self.current.kind == "clock":
                    self.deadline += 12
                    reward = " · +12s"
                elif self.current.kind == "sanctuary":
                    self.lives = min(5, self.lives + 1)
                    reward = " · vida restaurada"
            message = f"+{points:,} pontos · combo {self.combo}{reward}"
            if self.current.kind == "boss" and self.current.cleared:
                self.finish("won")
        else:
            self.lives -= 1
            self.combo = 0
            reason = "Tempo da pergunta esgotado" if expired else "Resposta incorreta"
            message = f"{reason}. Resposta: {question['answer']}"
            if self.lives <= 0:
                self.finish("lost")
        result = {"correct": correct, "points": points, "message": message,
                  "answer": question["answer"], "player": self.player + 1}
        self.question = None
        self.player = (self.player + 1) % len(self.scores)
        return result
