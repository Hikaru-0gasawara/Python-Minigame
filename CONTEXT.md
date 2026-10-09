# Dungeon Crawler

A competitive quiz dungeon crawler: players race through a procedurally generated dungeon, answering guardians' questions, and the first to escape wins. Canonical terms are English; on-screen text uses the player's chosen language.

## Language

### Places

**Dungeon**:
The generated place: rooms on an orthogonal grid joined by passages. Every Expedition gets a new one.
_Avoid_: Masmorra (on-screen only), board, level

**Room**:
One position in the Dungeon.
_Avoid_: casa, tile, space, cell

**Entrance**:
The room where every player starts an Expedition.
_Avoid_: Entrada (on-screen only), start

**Dead End**:
A room with a single passage that is not on the way to the exit. It may hold anything any other room can.
_Avoid_: beco, leaf

**Depth**:
The number of rooms between a room and the Entrance along the shortest path.
_Avoid_: distance, floor, distância, profundidade (on-screen only)

**Sector**:
A band of Depth with its own look, so players can tell how deep they are: shallow, middle or deep.
_Avoid_: zone, area, biome, setor (on-screen only)

**Seed**:
The value from which a Dungeon and everything placed in it is generated; it is shown to players so the same Dungeon can be replayed or shared.

**Map**:
A player's own top-down view of the Rooms they have Revealed; the minimap is a miniature of it.
_Avoid_: board, overview

### Play

**Expedition**:
One game: every player racing through the same Dungeon, ending when someone escapes.
_Avoid_: partida, run, match, game

**Turn**:
One player's go: a single move to a neighbouring Room, plus whatever that Room demands.
_Avoid_: round, rodada

**Difficulty**:
The mode chosen for an Expedition: Easy, Medium, Hard or Campaign (on-screen: Aventureiro, Guerreiro, Pesadelo, Campanha).
_Avoid_: Explorador, mode, level

**Tier**:
How hard a single Question is: easy, medium or hard. A Difficulty sets how often each Tier appears.
_Avoid_: difficulty (for questions), level

**ECO**:
The AI whose mind the Dungeon is. It speaks through its Guardians, and its Questions are tests; escaping through the Exit is escaping ECO.
_Avoid_: AM, the computer, the system

**Guardian**:
A statue through which ECO asks a Question to every player who enters its room.
_Avoid_: monster, enemy, boss

**Taunt**:
A short line ECO speaks through a Guardian before its Question.
_Avoid_: flavor text, fala (on-screen only), greeting

**Question**:
A single quiz prompt posed by a Guardian.
_Avoid_: pergunta (on-screen only), challenge

**Life**:
One of a player's three chances; losing the last sends the player back to the Entrance with all lives restored.
_Avoid_: vida (on-screen only), HP, heart

**Buff**:
A beneficial effect a player gains during an Expedition. Ward, Hex and Swap are held (one at a time, a new one replaces it); Haste and Insight apply at once.
_Avoid_: power-up, bonus

**Ward**:
A held Buff that cancels the penalty of the player's next wrong answer.

**Haste**:
A Buff that grants one extra move in the current Turn.

**Insight**:
A Buff that Reveals every Room within two passages of the player.

**Hex**:
A held Buff that makes a chosen opponent lose their next Turn.

**Swap**:
A held Buff that exchanges the player's position with a chosen opponent's.

**Debuff**:
A harmful effect a player suffers during an Expedition.
_Avoid_: penalty, curse

**Record**:
One of the five best escape times kept for a Difficulty between Expeditions, with its Seed, player count and date.
_Avoid_: high score, score, ranking

**Retreat**:
Being sent back to the Room the player came from.
_Avoid_: recuar (on-screen only), push back

### Room kinds

**Combat room**:
A room whose Guardian asks a plain Question, with no further effect.
_Avoid_: Terminal, battle

**Elite room**:
A room whose Guardian asks a hard-Tier Question and grants a Buff when cleared.
_Avoid_: Sobrecarga, overload

**Treasure room**:
A room with no Guardian that grants a Buff on each player's first visit.
_Avoid_: Cache, chest room

**Trap room**:
A room with no Guardian that inflicts a Debuff on each player's first visit.
_Avoid_: hazard

**Sanctuary**:
A room with no Guardian that restores one Life.
_Avoid_: Recuperação, shrine

**Empty room**:
A room with no Guardian and no effect.

**Mimic**:
A Trap room disguised as a Treasure room.

**Exit**:
The final room; its Guardian asks three Questions, answered one per Turn, and the first player to clear it wins the Expedition.
_Avoid_: boss, Núcleo, core

### Room states

All room states are tracked per player.

**Revealed**:
A room shown on a player's Map.
_Avoid_: discovered, seen

**Visited**:
A room a player has entered.
_Avoid_: explored

**Cleared**:
A room whose Guardian a player has answered correctly.
_Avoid_: completed, solved, concluída (on-screen only)
