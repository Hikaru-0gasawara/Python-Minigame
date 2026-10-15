# Sound is mixed in Python and streamed to the system

The Ambience has to play under the effects, but Windows' `winsound` plays one sound at a time: every voice blip would cut the music. We now synthesise everything at startup (effects and the Ambience, see ADR-0004 for the same choice in pixels), sum it in Python, chunk by chunk, and hand one endless 16-bit stream to the system: `waveOut` (winmm, through ctypes) on Windows, and on Linux a pipe into the first command-line player installed (`pw-cat`, `pacat`, `aplay`). A new effect cuts the previous effect, never the music. The levels are set so the sum never clips, so mixing is a plain addition.

## Considered Options

- **Keep `winsound`, add a second player for the music:** `winsound` cannot overlap sounds, and Windows has no other sound in the standard library.
- **A library (pygame, simpleaudio):** it mixes for us, but it is the game's first dependency and needs installing on every machine.
- **Audio files for the music:** better music than code can write, but only WAV reads without a library, at over a megabyte a minute, and every track would need a licence.

## Consequences

- The mixer runs on a thread and costs a little CPU all the time, even in silence.
- Sound latency is the queue behind the player: about 23 ms on Linux and 90 ms on Windows.
- The Windows output cannot be tested on Linux; it needs a run on Windows after every change to it.
