# 03: Competitive race core

**What to build:** The game becomes a race (ADR-0001). A Tk-free `Expedition` holds the Dungeon and one Player per participant, built from Difficulty, player count, Seed and an injected clock. Turns go in fixed order P1 to Pn, and each Turn is one move to a neighbouring Room. On entering a Room whose Guardian the player has not Cleared, a new never-repeated Question starts with the Difficulty's Question time. Running out of time counts as wrong. A correct answer Clears the Room for that player only. For now a wrong answer just ends the Turn (Tier penalties arrive in ticket 04). A player starting a Turn in an un-Cleared Room either answers a new Question or Retreats to the Room they came from. Every player who enters a Room faces its Guardian, whoever Cleared it before. The Exit's Guardian asks three Questions, one per Turn; progress is kept, and the first player to three hits wins.

Each player has their own Revealed, Visited and Cleared sets. Entering Reveals the Room and its neighbours for that player only. The Map and minimap show the active player's view, switch each Turn, and draw every player's position. A clear indicator shows whose Turn it is. Score, combo, speed bonus, the global clock and shared lives are removed. In this slice every Room other than Entrance and Exit is a Combat room. Camera, doors, walking transitions and reduced motion keep working, bound to the active player.

**Blocked by:** 01, 02.

**Status:** done

- [x] Turns rotate P1 to Pn; each Turn is one move, plus a Question when the Room demands one
- [x] Each Guardian questions every player who enters until that player Clears it; Cleared state is per player
- [x] Questions never repeat within an Expedition; Question timeout counts as wrong and ends the Turn
- [x] A player in an un-Cleared Room can answer again or Retreat on their Turn
- [x] The Exit needs three correct answers across Turns; progress survives leaving; the first to three wins and the Expedition ends
- [x] Revealed / Visited / Cleared are per player; the Map and minimap show only the active player's Revealed Rooms and passages, plus every player's position
- [x] The turn indicator identifies the active player; four players fit the minimum window
- [x] Score, combo, speed bonus, global clock and shared lives no longer exist in rules or screen
- [x] Invalid actions (wrong player, missing door, no Question, game over) are rejected without side effects
- [x] Rules are tested Tk-free through the Expedition's public actions and readable state; existing UI tests (portals, camera, transitions, reduced motion, callback cancellation) are rebased onto Turns
