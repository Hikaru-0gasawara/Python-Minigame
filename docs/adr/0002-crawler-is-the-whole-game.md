# The crawler replaces the classic board game

The project shipped two games: the classic dice board (`core.py` rules, `gui.py --board`, the terminal front-end in `__main__.py`) and the dungeon crawler. We are removing the classic board game and keeping only the crawler, which takes over the board-game feel through each player's top-down Map. The question bank, currently in `core.py`, moves to its own module because the crawler still needs it.
