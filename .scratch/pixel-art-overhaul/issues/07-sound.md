# 07: Sound

**What to build:** An audio module built on Windows' standard sound support. Short sounds are synthesised in code at startup and written once to a cache folder:
- voice blip;
- door;
- chest;
- trap;
- correct;
- wrong.

Playback is asynchronous, and a new sound cuts the previous one. The Guardian's dialogue plays a blip per revealed non-space character. Moves, chests, Traps and answers play their sounds. A mute toggle sits in the HUD. On systems without Windows sound support, every call is a silent no-op.

**Blocked by:** 05, 06.

**Status:** done

- [x] Dialogue blips play per revealed character; door, chest, trap, correct and wrong sounds play on their events
- [x] The mute toggle silences everything immediately
- [x] On non-Windows systems the game runs silently without errors
- [x] No sound file is committed; sounds are generated at startup
- [x] Covered by tests with an injected player: events produce the right calls, mute and non-Windows produce none

## Comments

- Done: `audio.py` synthesises the six sounds (11 ms) into `%TEMP%/ecos-sounds`, rewriting a file only when its bytes change. The HUD chip under the minimap ("SOM ●/○") and Alt+M toggle mute; muting also stops the sound already playing.
- A blip plays per batch of letters revealed in a frame (about one letter at 40/s). Completing the text at once, or reduced motion, plays one blip, not one per letter, since each new sound cuts the last anyway.
- A Mimic plays the trap sound. A Sanctuary heal and Hex/Swap have no sound because the ticket lists none.
