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

**Status:** ready-for-agent

- [ ] Dialogue blips play per revealed character; door, chest, trap, correct and wrong sounds play on their events
- [ ] The mute toggle silences everything immediately
- [ ] On non-Windows systems the game runs silently without errors
- [ ] No sound file is committed; sounds are generated at startup
- [ ] Covered by tests with an injected player: events produce the right calls, mute and non-Windows produce none
