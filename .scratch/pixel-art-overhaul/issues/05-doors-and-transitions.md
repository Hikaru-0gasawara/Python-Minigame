# 05: Doors and transitions

**What to build:** Doors come in three Sector styles (sliding blast door, rising rusted shutter, heavy vault door), each opening frame by frame, with a red lock light while the player cannot leave. Walking through a door:
1. The door opens.
2. The camera steps into the doorway at zooms of ×3, ×4, ×5, ×6, ×8 and ×10.
3. The view fades through a dither drawn at the size of one art pixel, after the zoom.
4. The next room arrives dark at ×4 and settles to ×3, its tubes stutter on and its Guardian boots.

Other transitions:
- **Looking:** a short horizontal pixel pan between facings.
- **Turn change:** a quick dither fade into the next player's room.
- **Preparation:** the next room's background is built while the door opens, so arrival never stalls.
- **Reduced motion:** every sequence becomes an immediate cut.

As today, the rules apply the move only at arrival, duplicate actions are ignored during a transition, and a timeout that passes the Turn cancels a walk in progress.

**Blocked by:** 03.

**Status:** done

- [x] Each Sector shows its own door style; doors open frame by frame and show the lock light when locked
- [x] The walk-through zooms in integer steps on the doorway and fades with art-pixel dithering
- [x] Arrival shows lights stuttering on and the Guardian booting
- [x] Looking pans; a Turn change fades to the next player's room
- [x] No visible pause on arrival: the next room is prepared during the door animation
- [x] Reduced motion cuts every sequence; duplicate input and Turn-passing timeouts are handled as today
- [x] Screen tests cover each transition completing once and the reduced-motion cut
