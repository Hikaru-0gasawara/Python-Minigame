# 02: Seeded Dungeon and the new Difficulty table

**What to build:** The menu offers the four Difficulties under their new on-screen names (Aventureiro, Guerreiro, Pesadelo, Campanha) and an optional Seed field. Starting an Expedition generates its Dungeon from a Seed: the typed one, or a random one when the field is empty or invalid. The Seed is shown on screen during play in a short human-friendly form. The same Seed and Difficulty always produce the same Dungeon. Dungeon sizes follow the spec's table (15 / 22 / 30 / 30 Rooms). Generation becomes a function of Seed and Difficulty that returns the Dungeon (Rooms, passages, Depth, Entrance, Exit, Room kinds), keeping the current orthogonal layout rules: loop at the Entrance, shortcuts, a guaranteed Dead End, and the Exit at maximum Depth with a single passage. The legacy `size` parameter and `floors` go away. The cooperative rules stay in place for now.

**Blocked by:** 01 (both rework the same modules).

**Status:** ready-for-agent

- [ ] The menu shows Aventureiro, Guerreiro, Pesadelo and Campanha, and an optional Seed field
- [ ] An empty or invalid Seed starts a random Seed; a valid one starts exactly that Dungeon
- [ ] The current Seed is visible on screen during the Expedition
- [ ] Same Seed + Difficulty yields an identical Dungeon (layout, Depths, Exit, Room kinds)
- [ ] Room counts are 15 / 22 / 30 / 30 for Easy / Medium / Hard / Campaign
- [ ] Generation invariants hold across many Seeds and every Difficulty: connected, reciprocal orthogonal passages, at least one loop, at least one Dead End, Exit at maximum Depth with one passage
- [ ] Code identifiers use the glossary (Difficulty Easy/Medium/Hard/Campaign, Depth, Exit, Entrance)
