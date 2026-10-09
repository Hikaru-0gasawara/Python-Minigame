# 07: Results screen and rematch

**What to build:** When a player wins, a results screen names the winner and shows the Seed. From there the group can rematch on the same Seed, start a new random Seed, or return to the menu. All pending animations and callbacks of the finished Expedition are cancelled.

**Blocked by:** 02 (needs the Seed), 03 (needs a winner).

**Status:** done

- [x] The results screen names the winning player (with their colour) and shows the Seed
- [x] "Same Seed" restarts an identical Dungeon with the same Difficulty and players
- [x] "New Seed" restarts with a fresh random Seed
- [x] Returning to the menu works and no callbacks from the old Expedition survive
- [x] Covered by screen tests
