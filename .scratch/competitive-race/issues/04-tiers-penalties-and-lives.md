# 04: Tiers, penalties and Lives

**What to build:** Questions are drawn by Tier according to the Difficulty's mix (spec table: Easy 70/25/5, Medium 40/45/15, Hard 15/40/45, Campaign 85/12/3), and the screen shows the Tier of the current Question. Each player has 3 Lives, shown for every player. A wrong answer or timeout applies the Tier penalty: easy loses a Life, medium makes the player lose their next Turn (skipped automatically in the turn order), and hard makes the player Retreat. Losing the last Life sends the player to the Entrance with 3 Lives, keeping their Map and Cleared Rooms. After a miss the correct answer is shown, and the penalty is announced.

**Blocked by:** 03.

**Status:** done

- [x] Over many draws, Tier frequencies match each Difficulty's mix within a tolerance
- [x] The current Question's Tier is visible on screen
- [x] Wrong easy costs a Life; wrong medium skips the next Turn; wrong hard Retreats; timeout behaves like wrong
- [x] Skipped Turns are passed over automatically and the skip clears
- [x] At 0 Lives the player returns to the Entrance with 3 Lives, Map and Cleared Rooms intact
- [x] Every player's Lives are shown and fit the minimum window with four players
- [x] The correct answer and the penalty are announced after a miss
- [x] Covered by Expedition rules tests and screen tests
