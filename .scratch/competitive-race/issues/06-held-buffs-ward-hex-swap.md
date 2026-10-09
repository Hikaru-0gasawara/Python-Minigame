# 06: Held Buffs: Ward, Hex and Swap

**What to build:** Buff draws now include the held Buffs. A player holds at most one held Buff; gaining another replaces it. Every player's held Buff is visible on screen. The active player can use their held Buff on their Turn.
- **Ward:** cancels the penalty of the player's next wrong answer and is consumed then. It does not protect against Hex or Trap and Mimic Debuffs.
- **Hex:** makes a chosen opponent lose their next Turn.
- **Swap:** exchanges positions with a chosen opponent; neither player's Room states change.

The screen offers a target choice for Hex and Swap, listing only opponents.

**Blocked by:** 05.

**Status:** done

- [x] Held Buffs are limited to one per player; a new one replaces the old
- [x] Every player's held Buff is visible and fits the minimum window with four players
- [x] Ward cancels exactly one wrong-answer penalty and nothing else
- [x] Hex skips the chosen opponent's next Turn; Swap exchanges positions without touching Room states
- [x] Hex and Swap cannot target the user; target choice is offered on screen
- [x] Using a Buff outside your Turn, or without holding one, is rejected without side effects
- [x] Covered by Expedition rules tests and screen tests
