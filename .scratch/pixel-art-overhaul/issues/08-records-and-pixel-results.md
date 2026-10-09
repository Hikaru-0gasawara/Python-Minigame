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

**Status:** ready-for-agent

- [ ] Elapsed time is measured from the Expedition's start to the win and frozen afterwards
- [ ] Records keep only the five best per Difficulty, sorted, with Seed, player count and date
- [ ] A missing or corrupt file means an empty scoreboard; saving never crashes the game
- [ ] The results screen is pixel art and announces a new Record with its rank
- [ ] Rematch, new Seed and menu work by click and keyboard and leave no old callbacks
- [ ] Records are tested with a temporary folder; elapsed time with the rules tests; the screen with screen tests
