"""Core rules for Python Trivia Adventure.

Pure logic: no printing, no input(). Both the terminal front-end (__main__.py)
and the graphical one (gui.py) drive this module and decide how to present it.
"""

import json
import os
import random
from typing import Callable, Dict, List, Optional, Tuple


# =========================
# Config
# =========================

class GameConfig:
    MIN_PLAYERS = 1
    MAX_PLAYERS = 4
    DICE_SIDES = 6
    QUIT_COMMANDS = {'q', 'quit', 'exit'}
    WIN_POSITIONS = {1: 36, 2: 46, 3: 56, 4: 123}
    DIFFICULTY_NAMES = {1: "Easy", 2: "Medium", 3: "Hard", 4: "Campaign"}


# =========================
# Question Bank + Difficulty
# =========================

class QuestionBank:
    def __init__(self, difficulty: str):
        self.difficulty = difficulty
        self.fallback = False
        self.questions = self._load_questions()

    def _load_questions(self):
        filename = f"{self.difficulty}_questions.json"
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__)) or os.getcwd()
            filepath = os.path.join(base_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list) or not data:
                    raise json.JSONDecodeError("Root must be a non-empty list", "", 0)
                return data
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.fallback = True
            return [
                {"question": "What is 2 + 2?", "answer": "4"},
                {"question": "What color is the sky on a clear day?", "answer": "blue"},
                {"question": "Which language is this game written in?", "answer": "python"},
            ]

    def get_random_question(self) -> Dict[str, str]:
        return random.choice(self.questions)


class DifficultyHandler:
    """Picks a question for a player, honouring campaign progression."""

    def __init__(self, difficulty: int):
        self.difficulty = difficulty
        if difficulty == 4:  # Campaign Mode
            self.easy_bank = QuestionBank("easy")
            self.medium_bank = QuestionBank("medium")
            self.hard_bank = QuestionBank("hard")
        else:
            diff_map = {1: "easy", 2: "medium", 3: "hard"}
            self.bank = QuestionBank(diff_map[difficulty])

    def bank_for(self, position: int = 0) -> QuestionBank:
        if hasattr(self, "bank"):
            return self.bank
        # Campaign progression thirds (123 tiles): 0-40 easy, 41-82 medium, 83+ hard
        if position < 41:
            return self.easy_bank
        if position < 83:
            return self.medium_bank
        return self.hard_bank

    def pick_question(self, position: int = 0) -> Dict[str, str]:
        return self.bank_for(position).get_random_question()

    def tier_name(self, position: int = 0) -> str:
        return self.bank_for(position).difficulty.capitalize()

    def using_fallback(self) -> bool:
        banks = [self.bank] if hasattr(self, "bank") else [self.easy_bank, self.medium_bank, self.hard_bank]
        return any(b.fallback for b in banks)

    @staticmethod
    def is_correct(question: Dict[str, str], answer: str) -> bool:
        return answer.strip().lower() == question["answer"].strip().lower()


# =========================
# Player
# =========================

class Player:
    def __init__(self, player_id: int, win_position: int):
        self.id = player_id
        self.position = 0
        self.win_position = win_position
        self.skip_next = False
        self.last_roll = 0

    def move(self, spaces: int) -> None:
        self.position = max(0, self.position + spaces)

    def has_won(self) -> bool:
        return self.position >= self.win_position


# =========================
# Board with curves + branches
# =========================

class Board:
    TILE_TYPES = [
        "normal", "bonus", "trap", "mystery", "quiz_boost",
        "swap", "push_down", "lift_up", "teleport", "skip", "double", "steal"
    ]
    TILE_SYMBOLS = {
        "normal": ".",
        "bonus": "+",
        "trap": "-",
        "mystery": "?",
        "quiz_boost": "*",
        "swap": "⇄",
        "push_down": "↓",
        "lift_up": "↑",
        "teleport": "✦",
        "skip": "⏭",
        "double": "✪",
        "steal": "⚔",
        "fork": "⚡",
    }
    TILE_NAMES = {
        "normal": "Normal",
        "bonus": "Bonus",
        "trap": "Trap",
        "mystery": "Mystery",
        "quiz_boost": "Quiz Boost",
        "swap": "Swap",
        "push_down": "Push Down",
        "lift_up": "Lift Up",
        "teleport": "Teleport",
        "skip": "Skip Turn",
        "double": "Double Trouble",
        "steal": "Steal",
        "fork": "Fork",
    }

    def __init__(self, size: int, difficulty: int):
        self.size = size
        self.difficulty = difficulty
        self.tiles: List = [self._random_tile() for _ in range(size)]
        if difficulty == 4:  # Campaign: add forks
            self._insert_branches(count=random.randint(3, 4))

    def _random_tile(self) -> str:
        # Slightly weighted randomness for readability and fun
        weights = {
            "normal": 0.35, "bonus": 0.12, "trap": 0.12, "mystery": 0.1,
            "quiz_boost": 0.07, "swap": 0.06, "push_down": 0.04, "lift_up": 0.04,
            "teleport": 0.03, "skip": 0.03, "double": 0.02, "steal": 0.02
        }
        choices = list(weights.keys())
        probs = list(weights.values())
        return random.choices(choices, probs, k=1)[0]

    def _insert_branches(self, count: int):
        interval = self.size // (count + 1)
        for n in range(1, count + 1):
            index = n * interval
            if 5 <= index < self.size - 6:
                self.tiles[index] = self._generate_fork()

    def _generate_fork(self) -> Dict[str, Tuple[List[str], List[str]]]:
        branch_a = random.choices(["bonus", "lift_up", "normal", "quiz_boost"], k=random.randint(3, 6))
        branch_b = random.choices(["trap", "steal", "mystery", "swap", "double"], k=random.randint(3, 6))
        return {"fork": (branch_a, branch_b)}

    @staticmethod
    def is_fork(tile) -> bool:
        return isinstance(tile, dict) and "fork" in tile

    def tile_at(self, position: int):
        """Tile a player stands on. Positions past the finish line are plain ground."""
        if 0 <= position < self.size:
            return self.tiles[position]
        return "normal"

    def kind_at(self, position: int) -> str:
        tile = self.tile_at(position)
        return "fork" if self.is_fork(tile) else tile

    def symbol_at(self, position: int) -> str:
        return self.TILE_SYMBOLS[self.kind_at(position)]

    def name_at(self, position: int) -> str:
        return self.TILE_NAMES[self.kind_at(position)]


# =========================
# Tile effects
# =========================

def _random_target(player: "Player", players: List["Player"]) -> "Player":
    candidates = [p for p in players if p is not player]
    return random.choice(candidates) if candidates else player


def apply_effect(
    board: Board,
    player: Player,
    roll: int,
    players: List[Player],
    choose_target: Optional[Callable[[Player, List[Player]], Player]] = None,
    choose_fork: Optional[Callable[[List[str], List[str]], str]] = None,
) -> Tuple[int, List[str]]:
    """Resolve the tile the player is standing on.

    Returns (spaces to move, log messages). Front-ends supply the two callbacks
    so the player can pick a target / a fork path however they like.
    """
    log: List[str] = []
    tile = board.tile_at(player.position)

    def pick_target() -> Player:
        if choose_target is None:
            return _random_target(player, players)
        return choose_target(player, [p for p in players if p is not player]) or player

    # Forks are resolved before normal movement
    if Board.is_fork(tile):
        branch_a, branch_b = tile["fork"]
        if choose_fork is None:
            choice = random.choice(["a", "b"])
        else:
            choice = (choose_fork(branch_a, branch_b) or "").strip().lower()
            if choice not in {"a", "b"}:
                choice = random.choice(["a", "b"])
                log.append(f"(Invalid choice — taking Path {choice.upper()} at random.)")
        length = len(branch_a) if choice == "a" else len(branch_b)
        player.move(length)
        log.append(f"⚡ Path {choice.upper()} taken — you advance {length} tiles!")
        return 0, log

    if tile == "normal":
        return roll, log
    if tile == "bonus":
        bonus = random.randint(1, 3)
        log.append(f"✨ Bonus! +{bonus} spaces.")
        return roll + bonus, log
    if tile == "trap":
        penalty = random.randint(1, 3)
        log.append(f"💀 Trap! -{penalty} spaces (min 0).")
        return max(0, roll - penalty), log
    if tile == "mystery":
        effect = random.choice(["+3", "-3", "x2", "0"])
        if effect == "+3":
            log.append("❓ Mystery: Surge forward +3.")
            return roll + 3, log
        if effect == "-3":
            log.append("❓ Mystery: Drag back -3 (min 0).")
            return max(0, roll - 3), log
        if effect == "x2":
            log.append("❓ Mystery: Double your roll!")
            return roll * 2, log
        log.append("❓ Mystery: No change.")
        return roll, log
    if tile == "quiz_boost":
        log.append("🧠 Quiz Boost: Double your move for a correct answer!")
        return roll * 2, log
    if tile == "swap":
        # The swap always spends the roll as well. Standing still here deadlocks
        # the match: two players parked on swap tiles would trade places forever,
        # and a solo player would never leave the tile at all.
        others = [p for p in players if p is not player]
        if others:
            other = random.choice(others)
            player.position, other.position = other.position, player.position
            log.append(f"⇄ Swap! You swapped positions with Player {other.id}, then move on.")
        else:
            log.append("⇄ Swap! Nobody else on the board — you just walk on.")
        return roll, log
    if tile == "push_down":
        target = pick_target()
        if target is player:
            log.append("↓ Push Down! No rivals around — the shove misses.")
            return roll, log
        penalty = random.randint(3, 6)
        target.position = max(0, target.position - penalty)
        log.append(f"↓ Push Down! Player {target.id} moves back {penalty}.")
        return roll, log
    if tile == "lift_up":
        target = pick_target()
        boost = random.randint(3, 6)
        target.position += boost
        who = "You jump" if target is player else f"Player {target.id} jumps"
        log.append(f"↑ Lift Up! {who} forward {boost}.")
        return roll, log
    if tile == "teleport":
        new_pos = random.randint(0, board.size - 1)
        log.append(f"✦ Teleport! You warp to tile {new_pos}.")
        player.position = new_pos
        return 0, log
    if tile == "skip":
        log.append("⏭ Skip Turn! You'll miss your next turn.")
        player.skip_next = True
        return roll, log
    if tile == "double":
        log.append("✪ Double Trouble! Roll counts double.")
        return roll * 2, log
    if tile == "steal":
        target = pick_target()
        if target is player:
            log.append("⚔ Steal! Nobody to rob — the loot stays put.")
            return roll, log
        stolen = getattr(target, "last_roll", 0)
        log.append(f"⚔ Steal! You steal +{stolen} from Player {target.id}.")
        return roll + stolen, log

    return roll, log


# =========================
# Turn engine
# =========================

class Game:
    """Holds the match state and walks it one turn at a time."""

    def __init__(self, num_players: int, difficulty: int):
        self.difficulty = difficulty
        self.win_position = GameConfig.WIN_POSITIONS[difficulty]
        self.players = [Player(i + 1, self.win_position) for i in range(num_players)]
        self.board = Board(self.win_position, difficulty)
        self.difficulty_handler = DifficultyHandler(difficulty)
        self.turn_index = 0
        self.round = 1
        self.winner: Optional[Player] = None

    @property
    def current_player(self) -> Player:
        return self.players[self.turn_index]

    def roll_dice(self) -> int:
        roll = random.randint(1, GameConfig.DICE_SIDES)
        self.current_player.last_roll = roll
        return roll

    def pick_question(self) -> Dict[str, str]:
        return self.difficulty_handler.pick_question(self.current_player.position)

    def consume_skip(self) -> bool:
        """True (and clears the flag) when the current player must sit this one out."""
        player = self.current_player
        if player.skip_next:
            player.skip_next = False
            return True
        return False

    def resolve_turn(
        self,
        correct: bool,
        roll: int,
        choose_target=None,
        choose_fork=None,
    ) -> List[str]:
        player = self.current_player
        if not correct:
            return [f"❌ Incorrect. Player {player.id} stays at {player.position}."]

        spaces, log = apply_effect(
            self.board, player, roll, self.players, choose_target, choose_fork
        )
        if spaces:
            player.move(spaces)
        log.append(
            f"Tile: {self.board.name_at(player.position).upper()} → "
            f"Player {player.id} at position {player.position}."
        )
        if player.has_won():
            self.winner = player
            log.append(f"🏆 Player {player.id} wins at position {player.position}!")
        return log

    def next_turn(self) -> None:
        self.turn_index = (self.turn_index + 1) % len(self.players)
        if self.turn_index == 0:
            self.round += 1
