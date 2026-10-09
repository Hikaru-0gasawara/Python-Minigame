# 09: Animated menu

**What to build:** The menu becomes a full-window animated pixel scene: parallax layers of server towers, ECO's pulsing core and hanging cables, plus sparks, scanlines and an occasional glitch.
- **Title:** ECOS sits centred in a large bitmap rendering.
- **Options:** a compact column holds Difficulty (Aventureiro, Guerreiro, Pesadelo, Campanha), players 1 to 4, an optional Seed field typed in pixel text, a mute toggle, the reduced-motion toggle and ENTRAR.
- **Records panel:** bottom-right, showing the five best times of the selected Difficulty.
- **Keyboard:** everything is navigable by keyboard.
- **Reduced motion:** stops the animation.
- **Cleanup:** leaving the menu cancels its callbacks, and the painted menu image is removed.

**Blocked by:** 02, 07, 08.

**Status:** ready-for-agent

- [ ] The menu is a full-window pixel scene with parallax layers and effects, scaled like the game screen
- [ ] The title is centred; Difficulty, players, Seed, mute, reduced motion and ENTRAR are in one column
- [ ] The Records panel shows the selected Difficulty's top five and updates when the Difficulty changes
- [ ] Every control works by keyboard; a typed Seed starts that Dungeon, an empty or invalid one a random Seed
- [ ] Reduced motion stops the animation; leaving the menu cancels every callback
- [ ] The painted menu image and its notes are removed
- [ ] Menu screen tests adapted and extended
