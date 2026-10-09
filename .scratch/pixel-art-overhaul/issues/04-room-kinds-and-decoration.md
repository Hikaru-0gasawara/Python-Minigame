# 04: Room kinds and decoration

**What to build:** Every Room kind gets its real prop, with the states the scene model chooses for the active player:

| Room kind | Prop and states |
|---|---|
| Elite | A bigger, armoured Guardian marked with ECO's emblem, in the same states as the Guardian |
| Treasure | An armoured data container, closed or open |
| Mimic | Identical to the Treasure container until the player has opened it, then mechanical jaws |
| Trap | Pressure plates and wall emitters, armed or spent |
| Sanctuary | A green-lit repair pod, idle or healing |
| Empty | Fallen server racks, cables and coolant puddles |
| Entrance | The elevator the players came down |
| Exit | The core gate, with 0 to 3 locks lit from the player's Exit hits |

Decorative props are chosen from the Seed per Room: flickering tubes, sparking cables, ECO propaganda screens (eye and static), steam vents and human graffiti. Particles add dust, sparks, steam and drips. Every sprite gets the same wear as the walls, and the horror stays suggested, not gory.

**Blocked by:** 01.

**Status:** done

- [x] Each Room kind shows its own prop; Elite and Exit are recognisable before any Question
- [x] Prop states follow the active player: a Mimic stays a chest until that player opened it; a Trap is spent after their visit; the Exit's locks match their Exit hits
- [x] Decorations and their placement are deterministic per Seed and differ between Rooms
- [x] Particles animate without changing the frame cost noticeably; reduced motion stops them
- [x] Scene model tests cover every kind and its per-player states
