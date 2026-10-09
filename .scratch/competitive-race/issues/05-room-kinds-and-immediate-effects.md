# 05: Room kinds and immediate effects

**What to build:** Every Dungeon places Room kinds from its Seed using weighted kinds (Combat most common; starting weights are the implementer's choice, to be tuned by playtests): Combat, Elite, Treasure, Mimic, Trap, Sanctuary and Empty. Any kind may sit in a Dead End.
- **Elite:** always asks a hard-Tier Question and grants a random Buff when Cleared.
- **Treasure:** grants a random Buff on each player's first visit. A **Mimic** looks like Treasure but inflicts a random Debuff.
- **Trap:** inflicts a random Debuff on first visit. Treasure, Trap and Mimic fire only on a player's first visit.
- **Sanctuary:** restores one Life (capped at 3). **Empty:** does nothing.

This slice delivers the immediate Buffs: Haste grants one extra move this Turn, and Insight Reveals every Room within two passages. It also delivers the Debuffs: Retreat, lose next Turn and lose a Life. Held Buffs (Ward, Hex, Swap) arrive in ticket 06, so draw only immediate Buffs here. Every effect is announced on screen. On the Map, Revealed-but-unvisited Rooms appear as silhouettes; Treasure rooms and Mimics show a chest icon.

**Blocked by:** 04.

**Status:** done

- [x] Room kinds are placed from the Seed; same Seed gives the same kinds and effects in the same Rooms
- [x] Elite always draws hard-Tier and grants a Buff when Cleared
- [x] Treasure / Trap / Mimic fire only on each player's first visit; Mimic is indistinguishable from Treasure before entering
- [x] Sanctuary restores one Life up to 3; Empty does nothing
- [x] Haste grants exactly one extra move; Insight Reveals Rooms within two passages for that player only
- [x] Debuffs Retreat, skip next Turn, or cost a Life, reusing ticket 04's rules (including return to Entrance at 0 Lives)
- [x] Unvisited Revealed Rooms render as silhouettes; Treasure and Mimic show a chest icon
- [x] Every Buff and Debuff is announced on screen
- [x] Covered by Expedition rules tests and screen tests
