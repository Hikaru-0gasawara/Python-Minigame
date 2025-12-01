import json
import os
import random
from typing import List, Dict, Optional

# =========================
# Config
# =========================

class GameConfig:
    MIN_PLAYERS = 1
    MAX_PLAYERS = 4
    DICE_SIDES = 6
    QUIT_COMMANDS = {'q', 'quit', 'exit'}
    WIN_POSITIONS = {1: 36, 2: 46, 3: 56, 4: 123}


# =========================
# Question Bank + Difficulty
# =========================

class QuestionBank:
    def __init__(self, difficulty: str):
        self.difficulty = difficulty
        self.questions = self._load_questions()

    def _load_questions(self):
        filename = f"{self.difficulty}_questions.json"
        try:
            base_dir = os.path.dirname(__file__) or os.getcwd()
            filepath = os.path.join(base_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise json.JSONDecodeError("Root must be a list", "", 0)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"[info] Using built-in questions for {self.difficulty} mode.")
            return [
                {"question": "What is 2 + 2?", "answer": "4"},
                {"question": "What color is the sky on a clear day?", "answer": "blue"},
                {"question": "Which language is this game written in?", "answer": "python"},
            ]

    def get_random_question(self):
        return random.choice(self.questions)


class DifficultyHandler:
    def __init__(self, difficulty: int):
        if difficulty == 4:  # Campaign Mode
            self.easy_bank = QuestionBank("easy")
            self.medium_bank = QuestionBank("medium")
            self.hard_bank = QuestionBank("hard")
        else:
            diff_map = {1: "easy", 2: "medium", 3: "hard"}
            self.bank = QuestionBank(diff_map[difficulty])

    def ask_question(self, position: int = 0):
        """Return True if answered correctly, False otherwise."""
        if hasattr(self, "bank"):
            return self._ask(self.bank)
        else:
            # Campaign progression thirds (123 tiles): 0-40 easy, 41-82 medium, 83+ hard
            if position < 41:
                return self._ask(self.easy_bank)
            elif position < 83:
                return self._ask(self.medium_bank)
            else:
                return self._ask(self.hard_bank)

    def _ask(self, bank: QuestionBank):
        q = bank.get_random_question()
        print(q["question"])
        ans = input("> ").strip().lower()
        return ans == q["answer"].lower()


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
        "steal": "⚔"
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

    def _generate_fork(self) -> Dict[str, List[str]]:
        branch_a = random.choices(["bonus", "lift_up", "normal", "quiz_boost"], k=random.randint(3, 6))
        branch_b = random.choices(["trap", "steal", "mystery", "swap", "double"], k=random.randint(3, 6))
        return {"fork": (branch_a, branch_b)}

    def display(self, players: List[Player]) -> None:
        row_len = random.randint(10, 15)
        indent = 0
        out = ["\nBoard:\n"]

        for i, tile in enumerate(self.tiles):
            if isinstance(tile, dict) and "fork" in tile:
                out.append("\n⚡ Fork Ahead! Choose your path:\n")
                continue

            # Clear player markers (P1|P2|...)
            players_here = [p for p in players if p.position == i]
            if players_here:
                symbol = "|".join([f"P{p.id}" for p in players_here])
            else:
                symbol = self.TILE_SYMBOLS[tile]

            out.append(f"[{symbol}] ")

            if (i + 1) % row_len == 0:
                indent = random.choice([0, 2, 4])
                out.append("\n" + " " * indent)
                row_len = random.randint(10, 15)

        print("".join(out) + "\n")

    def resolve_fork_choice(self, player: Player) -> None:
        tile = self.tiles[player.position]
        if not (isinstance(tile, dict) and "fork" in tile):
            return

        branch_a, branch_b = tile["fork"]
        a_preview = " ".join(f"[{self.TILE_SYMBOLS[t]}]" for t in branch_a)
        b_preview = " ".join(f"[{self.TILE_SYMBOLS[t]}]" for t in branch_b)

        print("⚡ You’ve reached a fork in the road!\n")
        print("Path A (safer):", a_preview)
        print("Path B (riskier):", b_preview)

        choice = input("Choose path A or B:\n> ").strip().lower()
        if choice not in {"a", "b"}:
            choice = random.choice(["a", "b"])
            print(f"(Invalid choice — taking Path {choice.upper()} at random.)")

        length = len(branch_a) if choice == "a" else len(branch_b)
        player.move(length)
        print(f"You advance {length} tiles via Path {choice.upper()}!\n")


# =========================
# Tile effects
# =========================

def apply_effect(board: Board, player: Player, roll: int, players: List[Player]) -> int:
    tile = board.tiles[player.position]

    # Forks are resolved before normal movement
    if isinstance(tile, dict) and "fork" in tile:
        board.resolve_fork_choice(player)
        return 0

    if tile == "normal":
        return roll
    if tile == "bonus":
        bonus = random.randint(1, 3)
        print(f"✨ Bonus! +{bonus} spaces.")
        return roll + bonus
    if tile == "trap":
        penalty = random.randint(1, 3)
        print(f"💀 Trap! -{penalty} spaces (min 0).")
        return max(0, roll - penalty)
    if tile == "mystery":
        effect = random.choice(["+3", "-3", "x2", "0"])
        if effect == "+3":
            print("❓ Mystery: Surge forward +3.")
            return roll + 3
        if effect == "-3":
            print("❓ Mystery: Drag back -3 (min 0).")
            return max(0, roll - 3)
        if effect == "x2":
            print("❓ Mystery: Double your roll!")
            return roll * 2
        print("❓ Mystery: No change.")
        return roll
    if tile == "quiz_boost":
        print("🧠 Quiz Boost: Double your move for correct answers!")
        return roll * 2
    if tile == "swap":
        others = [p for p in players if p != player]
        if others:
            other = random.choice(others)
            player.position, other.position = other.position, player.position
            print(f"⇄ Swap! You swapped positions with Player {other.id}.")
        return 0
    if tile == "push_down":
        target = _choose_target(player, players)
        penalty = random.randint(3, 6)
        target.position = max(0, target.position - penalty)
        print(f"↓ Push Down! Player {target.id} moves back {penalty}.")
        return roll
    if tile == "lift_up":
        target = _choose_target(player, players)
        boost = random.randint(3, 6)
        target.position += boost
        print(f"↑ Lift Up! Player {target.id} jumps forward {boost}.")
        return roll
    if tile == "teleport":
        new_pos = random.randint(0, board.size - 1)
        print(f"✦ Teleport! You warp to tile {new_pos}.")
        player.position = new_pos
        return 0
    if tile == "skip":
        print("⏭ Skip Turn! You’ll miss your next turn.")
        player.skip_next = True
        return roll
    if tile == "double":
        print("✪ Double Trouble! Roll counts double.")
        return roll * 2
    if tile == "steal":
        target = _choose_target(player, players)
        stolen = getattr(target, "last_roll", 0)
        print(f"⚔ Steal! You steal +{stolen} from Player {target.id}.")
        return roll + stolen

    return roll


def _choose_target(player: Player, players: List[Player]) -> Player:
    candidates = [p for p in players if p != player]
    if not candidates:
        return player
    print("Choose a player to target:")
    for p in candidates:
        print(f"[{p.id}] Player {p.id} (Position {p.position})")
    choice = input("> ").strip()
    if choice.isdigit():
        choice_id = int(choice)
        for p in candidates:
            if p.id == choice_id:
                return p
    chosen = random.choice(candidates)
    print(f"(Randomly targeting Player {chosen.id})")
    return chosen


# =========================
# Game loop
# =========================

class Game:
    def __init__(self, num_players: int, difficulty: int):
        self.difficulty = difficulty
        self.win_position = GameConfig.WIN_POSITIONS[difficulty]
        self.players = [Player(i + 1, self.win_position) for i in range(num_players)]
        self.board = Board(self.win_position, difficulty)
        self.difficulty_handler = DifficultyHandler(difficulty)
        self.legend_printed = False

    def play(self) -> None:
        print(f"Starting game with {len(self.players)} player(s).")
        print(f"Difficulty: {self.difficulty} — Win at {self.win_position} tiles.\n")
        self._print_legends_once()

        while True:
            self.board.display(self.players)
            for player in self.players:
                if not self._take_turn(player):
                    return
                if player.has_won():
                    print(f"🏆 Player {player.id} wins at position {player.position}!\n")
                    return

    def _take_turn(self, player: Player) -> bool:
        if player.skip_next:
            player.skip_next = False
            print(f"Player {player.id} skips this turn.\n")
            return True

        roll = random.randint(1, GameConfig.DICE_SIDES)
        player.last_roll = roll
        print(f"Player {player.id} rolled: {roll}")
        print("Answer correctly to move!")

        correct = self.difficulty_handler.ask_question(player.position)
        if correct:
            move_spaces = apply_effect(self.board, player, roll, self.players)
            if move_spaces:
                player.move(move_spaces)
            tile = self.board.tiles[player.position]
            tile_name = "FORK" if isinstance(tile, dict) else tile.upper()
            print(f"Tile: {tile_name} → Player {player.id} at position {player.position}.\n")
        else:
            print(f"Incorrect. Player {player.id} stays at {player.position}.\n")

        return True

    def _print_legends_once(self):
        if self.legend_printed:
            return
        legend = (
            "Legend:\n"
            "[.] Normal   [+] Bonus   [-] Trap\n"
            "[?] Mystery  [*] Quiz Boost   [⇄] Swap\n"
            "[↓] Push Down   [↑] Lift Up   [✦] Teleport\n"
            "[⏭] Skip Turn   [✪] Double   [⚔] Steal\n"
            "[P#] Player markers (e.g., P1, P2)\n"
        )
        print(legend)
        self.legend_printed = True


# =========================
# Entry point
# =========================

def get_valid_input(prompt: str, lo: int, hi: int) -> Optional[int]:
    while True:
        s = input(prompt).strip().lower()
        if s in GameConfig.QUIT_COMMANDS:
            return None
        if not s.isdigit():
            print("Please enter a number.")
            continue
        v = int(s)
        if lo <= v <= hi:
            return v
        print(f"Please enter a value between {lo} and {hi}.")

def main():
    print("🐍 Python Trivia Adventure\n")
    num_players = get_valid_input(
        f"Number of players [{GameConfig.MIN_PLAYERS}-{GameConfig.MAX_PLAYERS}] or 'q' to quit:\n> ",
        GameConfig.MIN_PLAYERS,
        GameConfig.MAX_PLAYERS
    )
    if num_players is None:
        print("Goodbye!")
        return

    print("\nDifficulty:\n[1] Easy\n[2] Medium\n[3] Hard\n[4] Campaign")
    difficulty = get_valid_input("Choose difficulty or 'q' to quit:\n> ", 1, 4)
    if difficulty is None:
        print("Goodbye!")
        return

    game = Game(num_players, difficulty)
    game.play()

if __name__ == "__main__":
    main()
