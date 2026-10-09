# Spec: Pixel-art overhaul

Status: ready-for-agent

## Problem Statement

ECOS plays like a game but does not look like one. The rooms are flat vector polygons redrawn every frame. The Guardian is a box with a "?". Treasure, Traps and Sanctuaries have no presence in the room; they exist only as names on buttons. Walking through a door is a zoom and a fade. The screen is a form: a scene in one corner, a sidebar of panels, Tk widgets for the answer and the doors. The menu is a painted illustration beside a settings form, with nothing that invites a rematch. Nothing tells the player where they are inside ECO, and nothing remembers how fast anyone escaped.

## Solution

Everything the player sees becomes pixel art, drawn by code at 320×200 and scaled up to fill the window. It is in the spirit of Risk of Rain, Isaac and Stardew Valley, set inside a decaying, dystopian giant computer that runs the AI ECO (after *I Have No Mouth, and I Must Scream*).

- **Sectors:** each Sector of Depth has its own look: cold concrete near the Entrance, rust in the middle, alarm-red at the bottom.
- **Rooms with presence:** every Room kind has a real, animated presence.
  - Guardians are statues that wake, speak and step aside.
  - Chests open, and Mimics bite.
  - Traps arm and fire.
  - Sanctuaries are repair pods.
  - The Exit is a gate with three locks.
- **Decoration:** props drawn from the Seed make every room different.
- **Doors:** each door opens frame by frame. The camera steps through it, and the next room arrives in the dark before its lights stutter on.
- **Guardian dialogue:** ECO speaks through the Guardian in a typewriter dialogue box with voice blips: a Taunt first, then the Question.
- **The screen:** the whole window is the dungeon, with a minimap top-right and RPG character cards along the bottom.
- **The menu:** an animated full-screen pixel scene with ECOS centred and the Records for the chosen Difficulty bottom-right.

## User Stories

### Looking and feeling like a game

1. As a player, I want the whole window to be the dungeon, so that it feels like a game and not a form.
2. As a player, I want crisp pixel art scaled by whole steps, so that no pixel is ever blurred or stretched.
3. As a player, I want black bars instead of distortion when the window's shape does not match, so that the art keeps its proportions.
4. As a player, I want the art to scale up when I enlarge the window, so that a big screen shows a big dungeon.
5. As a player, I want one consistent palette across the scene, HUD and menu, so that everything belongs to the same world.
6. As a player, I want the dungeon to feel like the inside of a dying machine, with concrete, rust, cables, fluorescent light and screens, so that the dystopian mood lands.
7. As a player, I want the horror to be suggested rather than gory, so that the game still works on a couch with friends.
8. As a player, I want the reduced-motion option to remove the animations without removing information, so that the game stays comfortable.

### Sectors and rooms

9. As a player, I want rooms near the Entrance to look like cold concrete, rooms in the middle to look rusted, and the deepest rooms lit in alarm red, so that I can feel how deep I am.
10. As a player, I want walls, floor and ceiling drawn in real perspective, with panels, seams, wear, rust drips, cracks, pipes, grates and puddles, so that rooms feel physical.
11. As a player, I want every room to differ in its details, decided by the Seed, so that no two rooms look identical.
12. As a player, I want the same Seed to produce the same rooms, props included, so that shared Seeds look the same for everyone.
13. As a player, I want decorative props such as flickering tubes, sparking cables, ECO propaganda screens, steam vents and human graffiti, so that the world feels lived-in and decayed.
14. As a player, I want light to flicker and particles to drift, so that rooms feel alive even when nobody moves.

### Room kinds made real

15. As a player, I want each Guardian to be a statue standing in its room, so that the keeper of the room is something I can see.
16. As a player, I want the Guardian's eye to light up when I enter, so that I know ECO is watching me.
17. As a player, I want the Guardian's eye to glow in the active player's colour while it waits for an answer, so that it is clear who is being tested.
18. As a player, I want a Guardian I have Cleared to step aside, with its eye gone green, so that passing it feels earned.
19. As a player, I want a Guardian someone else Cleared to still block me, so that the picture matches the rule that every player faces it.
20. As a player, I want the Elite Guardian to be bigger, armoured and marked with ECO's emblem, so that I recognise a harder Question before it is asked.
21. As a player, I want a Treasure room to hold an armoured data container that opens on my first visit, so that the Buff has a source.
22. As a player, I want a Mimic to look exactly like a Treasure container until I open it, and then reveal mechanical jaws, so that the trick is visible and memorable.
23. As a player, I want a Trap room to show pressure plates and wall emitters that fire on my first visit and stay spent afterwards, so that the Debuff has a cause.
24. As a player, I want a Sanctuary to be a green-lit repair pod that heals me, so that it reads as a place of rest.
25. As a player, I want an Empty room to be full of fallen server racks, loose cables and coolant puddles, so that a wasted trip still looks like something.
26. As a player, I want the Entrance to show the elevator or hatch we came down, so that the start of the run has a place.
27. As a player, I want the Exit to be a great core gate with three locks that light up as I answer its Guardian, so that my progress towards escaping is visible.
28. As a player, I want each room's look to reflect what I personally know and have done there, such as a chest I opened or a Guardian I passed, so that the scene matches my own Map.

### Doors and movement

29. As a player, I want doors to look different in each Sector (sliding blast doors, rising rusted shutters, heavy vault doors), so that Sectors feel distinct without revealing what lies behind.
30. As a player, I want a door to open frame by frame when I walk through it, so that moving feels physical.
31. As a player, I want the camera to step forward through the doorway in pixel-sized zoom steps and fade to dark, so that I feel I am passing into the next room.
32. As a player, I want the next room to arrive in the dark, its lights stuttering on and its Guardian booting up, so that each room has an entrance moment.
33. As a player, I want the fades to dither at the size of one art pixel, so that transitions stay in the pixel-art style.
34. As a player, I want no pause when entering a room, so that the next room is ready by the time the door has opened.
35. As a player, I want to look left and right with a short pixel pan, so that turning the camera is readable.
36. As a player, I want to click a door in the scene or use Alt + arrows to move, so that I do not need separate direction buttons.
37. As a player, I want arrows at the screen's edges to turn the camera, so that looking around is discoverable.
38. As a player, I want a locked door to show its red lock light, so that I know why I cannot leave.
39. As a player, I want a quick dither fade when the Turn passes to another player, so that I notice the view has switched to their room.

### Guardians speaking

40. As a player, I want the Question to come out of the Guardian in a dialogue box, so that ECO is the one testing me.
41. As a player, I want the text to appear letter by letter with a voice blip per letter, like Undertale or Pokémon, so that the Guardian has a voice.
42. As a player, I want ECO to say a short Taunt in Portuguese before the Question, chosen by Tier and Room kind, so that it has a personality.
43. As a player, I want to press Enter or click to finish the text instantly, so that slow typing never wastes my time.
44. As a player, I want the Question's timer to start only once the whole Question is on screen, so that reading speed is not penalised.
45. As a player, I want to type my answer inside the dialogue box, with a blinking cursor, so that answering stays in the same place.
46. As a player, I want Portuguese characters (ã, ç, é…) to display correctly, so that the text reads naturally.
47. As a player, I want long English questions to wrap neatly within the box, so that they are always readable.
48. As a player, I want the dialogue box to show the Question's Tier and what a wrong answer will cost, so that I can weigh the risk.
49. As a player, I want the Guardian to react to my answer (eye flash, glitch on a miss, stepping aside on a hit), so that the result is felt, not just read.

### HUD

50. As a player, I want a minimap in the top-right corner showing my Map, so that I can plan without leaving the scene.
51. As a player, I want the room's name, its Sector and whose Turn it is in the top-left corner, so that I always know where and who.
52. As a player, I want one character card per player along the bottom, with portrait colour, Lives, held Buff, Depth and Exit progress, so that the race is readable at a glance.
53. As a player, I want the active player's card raised and highlighted, so that the Turn is obvious.
54. As a player, I want Retreat and the use of my held Buff on my own card, with keyboard shortcuts, so that my actions are where my status is.
55. As a player, I want Buff and Debuff announcements to pop up in pixel text over the scene, so that I see what just happened.
56. As a player, I want the Seed visible in the HUD, so that I can share it at any time.
57. As a player, I want the HUD to fit four players at the minimum window size, so that a full couch can play.

### Menu

58. As a player, I want the menu to be an animated full-screen pixel scene, with server towers, ECO's pulsing core, cables and sparks, so that the game makes a first impression.
59. As a player, I want the ECOS title centred and large, so that the game has an identity.
60. As a player, I want Difficulty, players and Seed in a compact column, so that setting up is quick.
61. As a player, I want the Records for the chosen Difficulty in the bottom-right corner, as in Megabonk, so that I have a time to beat.
62. As a player, I want the menu fully usable with the keyboard, so that I never need the mouse.
63. As a player, I want the animation to stop when reduced motion is on, so that the menu stays comfortable.

### Records and results

64. As a player, I want the time from the start of an Expedition to the winner's escape recorded, so that fast escapes count.
65. As a player, I want the five best times per Difficulty kept between sessions, with Seed, player count and date, so that Records last.
66. As a player, I want the results screen to tell me when the escape set a Record, and where it ranks, so that it feels like an achievement.
67. As a player, I want a missing or damaged Records file to mean an empty scoreboard, never a crash, so that the game always starts.
68. As a player, I want the results screen in the same pixel style, with rematch on the same Seed, a new Seed and the menu, so that playing again is one key away.

### Sound

69. As a player, I want voice blips, door, chest, trap, correct and wrong sounds, so that actions have feedback.
70. As a player, I want a mute toggle, so that I can play silently.
71. As a player on a system without sound support, I want the game to run silently instead of failing, so that it still works.

### Developer

72. As a developer, I want sprites as character grids and small procedural drawings in the source, so that art is reviewable in a diff and needs no image files.
73. As a developer, I want what a room shows to be decided by a Tk-free function of the game state, so that visuals can be tested without a display.
74. As a developer, I want one palette module that every drawing uses, so that colours never drift.
75. As a developer, I want the bitmap font, the text layout and the dialogue pacing separated from the screen, so that they can be tested and reused by the menu.

## Implementation Decisions

- **Renderer.** Everything visible is drawn into one 320×200 indexed frame, then upscaled by the largest integer factor that fits the window and centred with black bars.
  - Tk does the alpha compositing (photo `copy` with overlay) and the integer zoom natively. The prototype measured about 3 ms per frame.
  - Python computes pixels only when a room, sprite or font glyph is built, never per frame.
  - The previous vector renderer and the alpha-veil helper are removed.
- **Palette.** One module holds the 32 colours and the named ramps: concrete, rust, amber, toxic green, alarm red, ECO cyan and violet. Each Sector's ramp stays within one hue family, so dithering never flickers between hues. Shading uses 4×4 ordered dithering between ramp steps. These were validated by the prototype.
- **Sectors.** A Room's Sector comes from its Depth relative to the Exit's Depth, in thirds: shallow, middle, deep. A Sector sets the wall, floor and ceiling ramps, the tube colour, the fog and rust amounts, and the door style. Nothing about a Sector changes the rules.
- **Pixel canvas.** A small indexed-colour canvas with these operations: set pixel, rectangle, line, polygon and ellipse fill with a dithered shading function, outer outline, blit, and PNG encoding to feed Tk. It is Tk-free.
- **Sprites.** Sprites are built in memory at startup from character grids (one character per palette colour, `.` for transparent) and procedural drawings, and cached per state and per Sector. The set:
  - Guardian: dormant, awake, listening (tinted by player colour), reacting to a miss, Cleared/stepping aside.
  - Elite Guardian: the same states, bigger and armoured.
  - Treasure container: closed and open.
  - Mimic: closed (identical to Treasure) and revealed.
  - Trap: armed and spent.
  - Sanctuary pod: idle and healing.
  - Empty-room debris set.
  - Entrance elevator.
  - Exit gate with 0 to 3 lit locks.
  - Doors: frame sequences in three Sector styles.
  - Decorative props: tubes, cables, propaganda screen (eye and static), vents, graffiti.
  - Particles: dust, sparks, steam, coolant drips.
  - Every prop is given the same wear as the walls. In the prototype the statue and doors looked too clean beside the walls.
- **Room background.** A function of (Seed, Room key, Sector, which doors exist) produces the static perspective background:
  - walls, floor and ceiling with panels and bevelled seams;
  - rust drips, cracks, pipes, grated floor plates and puddles;
  - closed side doors mapped onto the side walls in perspective.
  It also produces a lights-dimmed variant (broken tube) and a lights-off variant for arrivals and flicker. The next room's background is built during the door animation, so arrival never stalls.
- **Scene model.** A Tk-free function maps the Expedition state and the active player to what the scene must show:
  - the Room's Sector;
  - which doors exist in the current facing, and whether they are locked;
  - which kind-specific prop is shown, in which state, following that player's Visited/Cleared/appearance (for example a Mimic stays a chest until that player has opened it);
  - the decorative props from the Seed;
  - the Exit's lit locks, from the player's Exit hits;
  - the Guardian's state.
  The screen only draws what this model says.
- **Transitions.** These are presentation sequences driven by the screen; the rules still apply a move at arrival, as today.
  - **Walking through a door:** door opening frames, then zoom steps of ×3, ×4, ×5, ×6, ×8 and ×10 centred on the doorway, then a dither fade at the art-pixel size. The new room arrives dark at ×4, settles to ×3, the tubes stutter on and the Guardian boots.
  - **Looking:** a short horizontal pixel pan between facings.
  - **Turn change:** a quick dither fade.
  - **Reduced motion:** every sequence becomes an immediate cut.
- **Font and text.** A bitmap font of about 6×10 per glyph covers ASCII and the Portuguese accented letters, plus the symbols the HUD uses (hearts, arrows, ◆, ·). A layout helper wraps text to a pixel width and counts lines.
- **Typing answers.** The Tk Entry widget is gone: the screen captures key presses while a Question is open. Typing supports letters including accents, digits, space, Backspace and Enter, and draws a blinking cursor in the dialogue box.
- **Dialogue.** The dialogue box reveals the Taunt and then the Question at a fixed characters-per-second rate, with a voice blip per non-space character. Enter or a click completes the text at once. The Question's deadline is set only when the Question is fully shown.
  - This requires one rules change: the Expedition starts the Question's clock on demand, when the screen reports the text as shown, instead of at the moment the Question is drawn.
  - The box shows the Tier and the cost of a miss (or that Ward cancels it).
- **Taunts.** Short Portuguese lines spoken by ECO, chosen per Tier and Room kind (Combat, Elite, Exit), drawn from the Question stream so they follow the Seed. The content stays within the agreed tone: oppressive, no gore.
- **Screen layout.** One full-window canvas shows the pixel frame; the HUD is drawn into the same 320×200 frame.
  - **Top-left:** Room name, Sector and the Turn badge.
  - **Top-right:** the minimap, drawn from the active player's Map with silhouettes, chest icons and rival dots, keeping the current rules.
  - **Bottom:** the character cards.
  - **Above the cards:** the dialogue box, when a Guardian speaks.
  - **Edge arrows:** turn the camera.
  - **Doors:** clickable in the scene.
  - **Keyboard:** Alt + arrows move, Alt + Q/E look. Retreat and Buff use are on the active card, with Alt shortcuts.
  - **Removed:** the separate door buttons, the sidebar and the Tk labels.
- **Menu.** A full-window animated pixel scene: parallax layers of server towers, ECO's core and cables, plus sparks, scanlines and an occasional glitch.
  - The ECOS title is centred, in a large bitmap rendering.
  - A compact column holds Difficulty, players, an optional Seed field and ENTRAR.
  - The Records panel sits bottom-right for the selected Difficulty.
  - Everything is keyboard navigable, and animation stops with reduced motion.
  - The painted menu image and its asset notes are removed.
- **Results screen.** It is restyled as pixel art. It reports a new Record and its rank, and keeps the same three actions.
- **Records.** A Tk-free module loads and saves the five best times per Difficulty in a JSON file in the user's data folder; see ADR-0003.
  - It exposes: the top five for a Difficulty, and submitting a finished time, which returns the rank or none.
  - An unreadable file is treated as empty.
  - The Expedition exposes its elapsed time from start to win, using the injected clock.
- **Audio.** It uses Windows' standard sound module. Short sounds are synthesised in code at startup (blip, door, chest, trap, correct, wrong) and written once to a cache folder, then played asynchronously. Playing a new sound cuts the previous one, which is acceptable.
  - A mute toggle is offered in the menu and the HUD.
  - On other systems every sound call is a no-op.
- **Text and language.** All on-screen strings stay Portuguese, and code identifiers follow CONTEXT.md.

## Testing Decisions

- **What makes a good test:** good tests check behaviour through public functions and screen actions. They never compare whole images. Visual tests assert facts: which sprites, props and doors the scene model lists; that buffers use only palette indices and have the right size; that the same Seed gives the same pixels.
- **Seam 1: Expedition rules (existing).** It gains tests for the on-demand Question clock (no deadline until shown, then the full Question time) and for elapsed time at win. Prior art: the current rules tests.
- **Seam 2: Scene model and drawing (new, Tk-free).** It covers:
  - Sector from Depth.
  - Doors per facing, and locked state.
  - Kind props and their per-player states: a Mimic shows as Treasure until the player's first visit; a Trap is spent after the visit; a Guardian is Cleared only for the player who answered; the Exit locks follow Exit hits.
  - Decorations are deterministic per Seed.
  - Room buffers are deterministic and within the palette.
  - The font covers every character of the question bank and every Portuguese on-screen string.
  - Text wrapping fits the box width.
  - Dialogue pacing reveals characters over time and completes instantly on request.
- **Seam 3: Screens (Tk display, existing).** These adapt the current screen and menu tests:
  - scaling picks the largest integer factor and letterboxes;
  - the HUD fits four players at the minimum window;
  - typing, Backspace and Enter submit answers;
  - the timer starts only after the text is shown;
  - door clicks and Alt + arrows move;
  - the turn change switches the view;
  - transitions complete once, and reduced motion cuts them;
  - restart and menu cancel all callbacks;
  - the menu shows the Records of the selected Difficulty;
  - the results screen reports a new Record.
- **Seam 4: Records (file, Tk-free).** Tests use a temporary folder: ordering, keeping only five, per-Difficulty separation, the rank returned, and a corrupt or missing file read as empty.
- **Audio:** it is tested through an injected player: muting and non-Windows systems produce no calls.
- **Tests to delete:** tests of the removed vector renderer and the removed Tk widgets (door buttons, sidebar labels).

## Out of Scope

- **Rules and balance:** no changes beyond the on-demand Question clock and recording elapsed time.
- **Music and mixing:** not in this work; one sound plays at a time.
- **Translations** into English or Spanish, and translating the question bank.
- **Painted or AI-generated art**, image files in the repository, and new runtime dependencies.
- **Online multiplayer, player names and accounts.**
- **Gamepad support.**
- **Open decisions from the previous round:** the cheap flee, the hidden Exit, Sanctuary looping, and Hex/Swap in solo stay as they are.

## Further Notes

- The look was validated by a throwaway prototype: 320×200, the 32-colour palette, the hooded screen-faced Guardian, a blast door opening and the zoom-step walk-through, across three Sector looks. Verdict: style, statue, zoom steps and resolution approved. The only note was to give props the same wear as the walls. The prototype is kept on a throwaway branch, not in `main`.
- This spec carries out ADR-0004 (pixel art drawn by code) and ADR-0003 (Records stored locally). Vocabulary follows CONTEXT.md: ECO, Guardian, Taunt, Sector, Record.
- DESIGN.md's identity section and its menu prompt notes describe the old painted, non-fantasy direction; they need rewriting for the dystopian ECO world.
- Suggested ticket order:
  1. palette, pixel canvas, font and text layout;
  2. room background, Sectors and scene model;
  3. the full-window screen and HUD;
  4. sprites for each Room kind and the decorative props;
  5. doors and transitions;
  6. Guardian dialogue, Taunts and the on-demand clock;
  7. sound;
  8. Records;
  9. menu;
  10. results screen;
  11. docs.
