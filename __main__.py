"""Python Trivia Adventure — terminal front-end.

Run `python __main__.py` for the classic text board, or `python __main__.py --gui`
(same as `python gui.py`) for the graphical board.
"""

import random
import sys
from typing import List, Optional

# The board art is full of emoji; Windows consoles still default to cp1252.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from core import Board, DifficultyHandler, GameConfig, Game, Player


# =========================
# Terminal rendering
# =========================

def display_board(board: Board, players: List[Player]) -> None:
    row_len = random.randint(10, 15)
    indent = 0
    out = ["\nBoard:\n"]

    for i, tile in enumerate(board.tiles):
        if Board.is_fork(tile):
            out.append("\n⚡ Fork Ahead! Choose your path:\n")
            continue

        # Clear player markers (P1|P2|...)
        players_here = [p for p in players if p.position == i]
        if players_here:
            symbol = "|".join([f"P{p.id}" for p in players_here])
        else:
            symbol = Board.TILE_SYMBOLS[tile]

        out.append(f"[{symbol}] ")

        if (i + 1) % row_len == 0:
            indent = random.choice([0, 2, 4])
            out.append("\n" + " " * indent)
            row_len = random.randint(10, 15)

    print("".join(out) + "\n")


LEGEND = (
    "Legend:\n"
    "[.] Normal   [+] Bonus   [-] Trap\n"
    "[?] Mystery  [*] Quiz Boost   [⇄] Swap\n"
    "[↓] Push Down   [↑] Lift Up   [✦] Teleport\n"
    "[⏭] Skip Turn   [✪] Double   [⚔] Steal\n"
    "[P#] Player markers (e.g., P1, P2)\n"
)


# =========================
# Terminal prompts (callbacks handed to the core rules)
# =========================

def console_choose_target(player: Player, candidates: List[Player]) -> Player:
    if not candidates:
        return player
    print("Choose a player to target:")
    for p in candidates:
        print(f"[{p.id}] Player {p.id} (Position {p.position})")
    choice = input("> ").strip()
    if choice.isdigit():
        for p in candidates:
            if p.id == int(choice):
                return p
    chosen = random.choice(candidates)
    print(f"(Randomly targeting Player {chosen.id})")
    return chosen


def console_choose_fork(branch_a: List[str], branch_b: List[str]) -> str:
    a_preview = " ".join(f"[{Board.TILE_SYMBOLS[t]}]" for t in branch_a)
    b_preview = " ".join(f"[{Board.TILE_SYMBOLS[t]}]" for t in branch_b)
    print("⚡ You've reached a fork in the road!\n")
    print("Path A (safer):", a_preview)
    print("Path B (riskier):", b_preview)
    return input("Choose path A or B:\n> ").strip().lower()


# =========================
# Game loop
# =========================

def play(game: Game) -> None:
    print(f"Starting game with {len(game.players)} player(s).")
    print(f"Difficulty: {game.difficulty} — Win at {game.win_position} tiles.\n")
    print(LEGEND)
    if game.difficulty_handler.using_fallback():
        print("[info] Some question files were missing — using built-in questions.\n")

    while True:
        if game.turn_index == 0:
            display_board(game.board, game.players)

        player = game.current_player
        if game.consume_skip():
            print(f"Player {player.id} skips this turn.\n")
            game.next_turn()
            continue

        roll = game.roll_dice()
        print(f"Player {player.id} rolled: {roll}")
        print("Answer correctly to move!")

        question = game.pick_question()
        print(question["question"])
        answer = input("> ")
        correct = DifficultyHandler.is_correct(question, answer)

        for line in game.resolve_turn(correct, roll, console_choose_target, console_choose_fork):
            print(line)
        print()

        if game.winner:
            return
        game.next_turn()


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
    if "--gui" in sys.argv:
        import gui
        gui.main()
        return

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

    play(Game(num_players, difficulty))


if __name__ == "__main__":
    main()
