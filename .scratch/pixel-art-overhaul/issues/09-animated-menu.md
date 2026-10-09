# 09: Animated menu

**What to build:** The menu becomes a full-window animated pixel scene: parallax layers of server towers, ECO's pulsing core and hanging cables, plus sparks, scanlines and an occasional glitch.
- **Title:** ECOS sits centred in a large bitmap rendering.
- **Options:** a compact column holds Difficulty (Aventureiro, Guerreiro, Pesadelo, Campanha), players 1 to 4, an optional Seed field typed in pixel text, a mute toggle, the reduced-motion toggle and ENTRAR.
- **Records panel:** bottom-right, showing the five best times of the selected Difficulty.
- **Keyboard:** everything is navigable by keyboard.
- **Reduced motion:** stops the animation.
- **Cleanup:** leaving the menu cancels its callbacks, and the painted menu image is removed.

**Blocked by:** 02, 07, 08.

**Status:** done

- [x] The menu is a full-window pixel scene with parallax layers and effects, scaled like the game screen
- [x] The title is centred; Difficulty, players, Seed, mute, reduced motion and ENTRAR are in one column
- [x] The Records panel shows the selected Difficulty's top five and updates when the Difficulty changes
- [x] Every control works by keyboard; a typed Seed starts that Dungeon, an empty or invalid one a random Seed
- [x] Reduced motion stops the animation; leaving the menu cancels every callback
- [x] The painted menu image and its notes are removed
- [x] Menu screen tests adapted and extended

## Comments

- Done. `menu_art.py` builds the Tk-free layers: the backdrop with its floor, far and near towers wrapping at 3 and 9 px/s, six frames of ECO's pulsing core, and the cables whose copper ends throw the sparks. Scanlines are baked in, since the layers only slide sideways. A glitch tears a few bands now and then. The layers are encoded once per run (`menu_ui.art`).
- `menu_ui.Setup` is one `PixelView` canvas. The title `ECOS` is drawn at ×4 by Tk's zoom. The column (Difficulty, players, Seed, sound, motion, ENTRAR) sits at the left, the Records bottom-right and the core top-right. Up, Down and Tab move between rows, Left and Right change a value, Enter or space takes the row, the Seed takes hex digits and `-`, and F1 opens the help. Hover and click work too.
- The Tk "Como jogar" dialog stays, opened with F1 or by clicking the footer, so the help is not lost. The Records lines leave out the date to fit beside the column.
- `assets/` is deleted. README and DESIGN.md still mention the old menu; ticket 10 rewrites them.
