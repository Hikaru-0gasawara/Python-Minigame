# The game is pixel art drawn by code at 320×200

The rooms were vector polygons redrawn every frame, and the menu was an AI-painted illustration. We now draw everything the player sees, scene and HUD, into a 320×200 frame with a fixed 32-colour palette, and upscale it by the largest integer factor that fits the window. Sprites are character grids and procedural drawings in the source, built in memory at startup; there are no image files to regenerate and no new dependency. Tk composites the layers and does the integer zoom natively, so a frame costs a few milliseconds; Python only computes a room's pixels once, when the room is built.

## Considered Options

- **Refined vector art:** smooth edges and free scaling clash with the retro pixel style wanted (Risk of Rain, Isaac, Stardew).
- **Vector architecture with pixel props:** the mix of smooth walls and hard pixels looked wrong.
- **AI-generated pixel art:** richer stills, but it spends credits and cannot keep a statue consistent across the frames of an animation.

## Consequences

- The Tk text entry gives way to text drawn with our own bitmap font, so typing answers is handled by the screen.
- A prototype that settled this decision lives on a throwaway branch, not in `main`.
