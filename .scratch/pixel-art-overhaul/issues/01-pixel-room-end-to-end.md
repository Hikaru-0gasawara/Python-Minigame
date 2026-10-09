# 01: Pixel-art room end to end

**What to build:** The room scene becomes pixel art drawn by code (ADR-0004), shown inside the current screen layout. The pieces:
- **Palette module:** the 32 colours and per-Sector ramps (one hue family per ramp), with 4×4 ordered dithering.
- **Pixel canvas:** Tk-free. Set pixel, rectangles, lines, shaded polygons and ellipses, outer outline, blit and PNG encoding.
- **Sector:** derived from a Room's Depth relative to the Exit's Depth, in thirds.
- **Room background:** built from (Seed, Room key, Sector, existing doors), with:
  - perspective walls, floor and ceiling with bevelled panel seams;
  - rust drips, cracks, pipes, grated plates and puddles;
  - closed side doors in perspective;
  - lights-dimmed and lights-off variants.
- **Scene model:** a Tk-free function from the Expedition state and the active player to the Sector, the doors visible in the current facing (with their locked state), and the Guardian's state.
- **Basic Guardian statue:** the hooded concrete sentinel with a screen face, with the same wear as the walls, in three states: dormant, listening, Cleared.

The screen composes background and sprites with Tk's photo copy and shows the 320×200 frame at the largest integer zoom that fits the current scene area. Doors stay clickable through the scene model's door regions. The vector renderer and the alpha-veil helper are removed, and moving between rooms is a plain cut until ticket 05. The prototype on branch `prototype/pixel-room` is the reference.

**Blocked by:** None (can start immediately).

**Status:** done

- [x] Rooms render as 320×200 pixel art in all three Sector looks, integer-scaled without blur
- [x] Same Seed and Room give identical pixels; buffers contain only palette indices
- [x] Sector is computed from Depth in thirds and drives ramps, fog and rust
- [x] The scene model lists exactly the doors that exist in the current facing, with locked state, and the Guardian's state per player
- [x] Doors are clickable and Alt + arrows still move; looking still rotates which doors are shown
- [x] The Guardian statue shows dormant, listening and Cleared states, and its wear matches the walls
- [x] The vector room renderer and alpha veil are gone; existing screen tests pass after adaptation
- [x] Scene model and pixel buffers are covered by Tk-free tests
