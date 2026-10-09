# 08: Records and the pixel-art results screen

**What to build:** The Expedition exposes its elapsed time from start to the winner's escape, using its injected clock. A Tk-free Records module keeps the five best times per Difficulty, each with Seed, player count and date, in a JSON file in the user's data folder (ADR-0003). It returns the top five for a Difficulty, and submitting a time returns its rank or none. A missing or unreadable file reads as empty and never crashes the game.

The results screen is redrawn in pixel art with the bitmap font. It shows:
- the winner in their colour;
- Difficulty and Seed;
- each player's line;
- a "new Record" notice with its rank;
- the three actions: rematch on the same Seed, new Seed, menu.

The three actions work by keyboard too.

**Blocked by:** 03.

**Status:** done

- [x] Elapsed time is measured from the Expedition's start to the win and frozen afterwards
- [x] Records keep only the five best per Difficulty, sorted, with Seed, player count and date
- [x] A missing or corrupt file means an empty scoreboard; saving never crashes the game
- [x] The results screen is pixel art and announces a new Record with its rank
- [x] Rematch, new Seed and menu work by click and keyboard and leave no old callbacks
- [x] Records are tested with a temporary folder; elapsed time with the rules tests; the screen with screen tests

## Comments

- Done. `Expedition.elapsed` runs from construction and freezes at the escape (`won_at`). `records.py` keeps `%APPDATA%/ECOS/records.json`, or `~/.local/share/ECOS` elsewhere. It writes through a temp file and `os.replace`. Any malformed file reads as empty. `DungeonApp.show_results` submits the time and passes the rank on.
- The results screen is the winner's room, dimmed, behind a pixel panel. Arrows and Tab pick an action, Enter or space takes it, Escape goes to the menu, and a click works too. It has no `after` loop, and its bindings sit on its own canvas.
- The font has no `º`, so the rank shows as `★ NOVO RECORDE · #2`.
- If saving fails (an unwritable folder), the rank is still announced but not kept.
