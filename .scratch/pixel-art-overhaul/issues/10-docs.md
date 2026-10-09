# 10: Documentation for the ECO world

**What to build:** Rewrite the README and DESIGN.md for the pixel-art, dystopian ECO world.
- **README:** describes the look, the full-window screen and its controls (door clicks, Alt shortcuts, typing answers), the Guardian's dialogue, Sectors, Records and the scoreboard, sound and mute, and the module layout.
- **DESIGN.md:** replaces the painted, non-fantasy identity and the menu prompt notes with the ECO direction (inside a dying giant computer, suggested horror, Risk of Rain, Isaac and Stardew references), records this round, and updates the proposed next rounds.
- **assets/ folder:** loses its notes about the removed painted image.

Both use CONTEXT.md vocabulary for concepts and the on-screen Portuguese names.

**Blocked by:** 01, 02, 03, 04, 05, 06, 07, 08, 09.

**Status:** done

- [x] The README matches the shipped game, including controls, Records and sound
- [x] DESIGN.md describes the ECO direction and this round, and no longer describes the painted menu or the vector rooms
- [x] No documentation references removed files
- [x] Terms match CONTEXT.md; on-screen names match the UI

## Comments

- Done. The README covers the look, Sectors, the Guardian's dialogue, the rooms as they appear in the scene, the controls (door clicks, the behind tab, Alt shortcuts, typing answers, Esc), the menu, Records, sound and mute, and every module. Tests run with `python -m unittest -v`.
- DESIGN.md has a new "Identidade: dentro de ECO" section. Rounds 2 and 3 shrink to what survived them (the camera and walk-through rules). Round 5 is recorded, and the next rounds are updated: balancing (the round-4 open decisions), the quiz, translations, music and accessibility with gamepad, and special modes.
- `assets/` was already removed in ticket 09. The docs now say "expedição" and avoid "beco", following CONTEXT.md. The "Leitura das sete imagens" section stays, as the record of the original references.
