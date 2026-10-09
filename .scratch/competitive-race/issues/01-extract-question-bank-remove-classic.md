# 01: Extract the question bank and remove the classic game

**What to build:** Launching the game goes straight to the crawler. The classic board game (its rules, Tk board, terminal front-end, launch flags and tests) is gone. The question bank lives in its own module: banks keyed by Tier (easy, medium, hard), backed by the existing question files plus the built-in fallback, with answer checking. Drawing takes a Tier and a random source, and never repeats a Question within one Expedition; an exhausted Tier resets its pool. The UI frame currently named `Expedition` is renamed `ExpeditionScreen`, freeing the name for the rules (ticket 03). The game otherwise plays exactly as it does today. See ADR-0002 and the spec.

**Blocked by:** None (can start immediately).

**Status:** done

- [x] The default launch (and the Windows launcher) opens the crawler menu; the classic board, the terminal mode and their flags no longer exist
- [x] The question bank module loads all three Tiers from the question files, falls back to built-in questions when a file is missing, and checks answers as before
- [x] Drawing never repeats a Question within one Expedition until that Tier's pool is exhausted, then resets
- [x] The UI frame is renamed `ExpeditionScreen` everywhere, tests included
- [x] Classic-game tests are deleted (there were none); the remaining dungeon, UI and menu tests pass
- [x] Question bank behaviour (Tier loading, fallback, no-repeat draws) is covered by tests
