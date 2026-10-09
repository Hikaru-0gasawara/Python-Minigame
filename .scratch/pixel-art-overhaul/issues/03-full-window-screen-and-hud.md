# 03: Full-window screen and HUD

**What to build:** The Expedition screen becomes one full-window canvas showing the 320×200 frame, scaled by the largest integer factor that fits and letterboxed with black. The HUD is drawn into the frame with the bitmap font:
- **Top-left:** the Room name, Sector and Turn badge.
- **Top-right:** the minimap, from the active player's Map, with silhouettes, chest icons and rival dots.
- **Bottom:** one character card per player, showing colour, Lives, held Buff, Depth and Exit progress. The active card is raised.
- **Screen edges:** arrows to turn the camera.
- **Announcements:** pixel-text pop-ups for Buffs, Debuffs and results.
- **Seed:** always visible.
- **Answer box:** a simple box where the active player types (letters with accents, digits, space, Backspace, Enter) with a blinking cursor. The Guardian's dialogue arrives in ticket 06.

Retreat and the use of a held Buff move onto the active card, by click and by Alt shortcuts. Moving is by clicking doors or with Alt + arrows, and looking with the edge arrows or Alt + Q/E. The sidebar, the door buttons and every Tk widget on this screen are removed.

**Blocked by:** 01, 02.

**Status:** ready-for-agent

- [ ] The whole window is the scene; the scale is the largest integer that fits and the rest is black
- [ ] The minimap shows only the active player's Map and switches each Turn
- [ ] Four player cards fit at the minimum window; the active card is clearly marked
- [ ] Typing, Backspace and Enter answer Questions; accents work; no Tk Entry remains
- [ ] Retreat and Hex/Swap targets work from the active card by click and shortcut
- [ ] Door clicks, Alt + arrows, edge arrows and Alt + Q/E all work
- [ ] Announcements and the Seed are visible in pixel text
- [ ] Screen tests adapted: scaling, HUD fit, input, movement, turn switch, callback cleanup
