# Spec: Competitive race

Status: ready-for-agent

## Problem Statement

The game is a cooperative quiz crawler. Up to four people share one clock, one pool of lives and one combo, and they take turns answering on behalf of the team. Scores are individual, but nobody can win or lose against anyone else, so the couch-party energy the players want never shows up. Every Expedition also feels alike. The classic board game still ships beside the crawler, which splits the project in two. The vocabulary in the code (`combat`, `boss`, `depth`, `floors`, a `Dungeon` class that is both the place and the run) no longer matches what the game is.

## Solution

The crawler becomes the whole game, and it becomes a race. Every player starts at the Entrance of the same freshly generated Dungeon. Each Turn, the active player moves one Room. If that Room has a Guardian the player has not yet Cleared, the player answers its Question. Wrong answers cost a Life, a Turn or a Retreat, depending on the Question's Tier. Treasure rooms, Mimics, Trap rooms, Elite rooms and Sanctuaries hand out Buffs and Debuffs. Some Buffs strike opponents. The first player to answer the Exit's Guardian three times wins.

Each player keeps their own Map, which shows only what they have Revealed. Every Dungeon comes from a Seed that is shown on screen and can be typed in to replay or share it. Difficulty sets the Dungeon's size and how often each Tier of Question appears. The classic board game is removed.

## User Stories

### Starting an Expedition

1. As a player, I want to choose a Difficulty (Aventureiro, Guerreiro, Pesadelo, Campanha), so that the Expedition matches my group's skill.
2. As a player, I want to choose 1 to 4 players, so that I can play alone or race friends on one screen.
3. As a player, I want every Expedition to generate a new Dungeon by default, so that no two games are the same.
4. As a player, I want to see the Seed of the current Expedition, so that I can share it with a friend.
5. As a player, I want to type a Seed in the menu, so that I can replay a Dungeon or take a friend's challenge.
6. As a player, I want the same Seed and Difficulty to produce the same Dungeon, with the same Room kinds and effects in the same places, for anyone, so that shared challenges are fair.
7. As a player, I want an invalid or empty Seed field to fall back to a random Seed, so that I can always start playing.
8. As a solo player, I want to race the Dungeon alone, so that the game still works without friends.

### Dungeon

9. As a player, I want Easy Dungeons to be the smallest and Hard and Campaign Dungeons the largest, so that the length of an Expedition fits its Difficulty.
10. As a player, I want the Dungeon to have forks, loops and Dead Ends, so that choosing a route matters.
11. As a player, I want a Dead End to look like any other route until I reach it, so that exploring is a gamble.
12. As a player, I want a Dead End to be able to hold any Room kind, so that a wasted trip can still pay off or hurt.
13. As a player, I want the Exit to be reachable from the Entrance, so that every Expedition can be won.
14. As a player, I want the Exit to be far from the Entrance by Depth, so that the race has length.
15. As a player, I want passages to work in both directions, so that I can always walk back.

### Turns

16. As a player, I want turns to go in a fixed order, P1 to Pn, so that I always know who is next.
17. As a player, I want my Turn to be a single move to a neighbouring Room plus whatever that Room demands, so that turns stay short.
18. As a player, I want a skipped Turn to be passed over automatically, so that play keeps flowing.
19. As a player, I want a clear indicator of whose Turn it is, so that the wrong person never answers.
20. As a player, I want to move freely through Rooms I have already Cleared, so that backtracking costs only the move.
21. As a player, I want to share a Room with other players without any effect, so that crowding never blocks me.
22. As a player in a Room I have not Cleared, I want to choose between answering a new Question and retreating to the Room I came from, so that I am never trapped.

### Guardians and Questions

23. As a player, I want every player who enters a Room to face its Guardian, even after someone else Cleared it, so that nobody rides on another player's answer.
24. As a player, I want each encounter to draw a new Question that has not appeared in this Expedition, so that watching other players' Turns never gives away an answer.
25. As a player, I want to see the Tier of the Question I am answering, so that I know what a wrong answer will cost.
26. As a player, I want a timer on each Question, so that stalling is not a strategy.
27. As a player, I want running out of time to count as a wrong answer, so that the timer has teeth.
28. As a player, I want the timer to run only during my own Question, so that other players' thinking never costs me time.
29. As a player, I want to see the correct answer after I miss, so that I learn something.

### Penalties and Lives

30. As a player, I want to start with 3 Lives, so that I can afford a few mistakes.
31. As a player, I want a wrong easy-Tier answer to cost me a Life, so that missing easy Questions hurts the most.
32. As a player, I want a wrong medium-Tier answer to cost me my next Turn, so that the penalty scales with how hard the Question was.
33. As a player, I want a wrong hard-Tier answer to make me Retreat, so that attempting hard Questions is not too punishing.
34. As a player, I want losing my last Life to send me back to the Entrance with all Lives restored, so that I am set back but never eliminated.
35. As a player, I want my Map and my Cleared Rooms to survive a return to the Entrance, so that I can catch up quickly.

### Difficulty and Tiers

36. As a player on Easy, I want mostly easy-Tier Questions, some medium and rare hard ones, so that the game feels approachable.
37. As a player on Medium, I want a balanced mix of Tiers, so that the challenge grows.
38. As a player on Hard, I want hard-Tier Questions to be the most common, so that it lives up to Pesadelo.
39. As a player on Campaign, I want a Hard-sized Dungeon with almost only easy-Tier Questions, so that the mode is about exploring.

### Room kinds

40. As a player, I want Combat rooms whose Guardian asks a Question, so that progress is earned.
41. As a player, I want Elite rooms whose Guardian always asks a hard-Tier Question and grants a Buff when Cleared, so that I can take a risk for a reward.
42. As a player, I want Treasure rooms to give me a random Buff on my first visit, so that exploring pays.
43. As a player, I want some Treasure rooms to be Mimics that give a random Debuff instead, so that greed carries risk.
44. As a player, I want Trap rooms to give me a random Debuff on my first visit, so that the Dungeon has hazards.
45. As a player, I want Sanctuaries to restore one Life, so that I can recover.
46. As a player, I want Empty rooms that do nothing, so that not every Room is an event.
47. As a player, I want Treasure, Trap and Mimic effects to fire only on my first visit, so that I cannot farm them and a second visit does not punish me again.

### Buffs and Debuffs

48. As a player, I want Ward to cancel the penalty of my next wrong answer, so that I can gamble on a risky Room.
49. As a player, I want Ward to protect only against wrong-answer penalties, not against Hex or traps, so that the rules stay simple.
50. As a player, I want Haste to give me one extra move this Turn, so that I can pull ahead.
51. As a player, I want Insight to Reveal every Room within two passages of me, so that I can plan a route.
52. As a player, I want Hex to make a chosen opponent lose their next Turn, so that I can slow the leader.
53. As a player, I want Swap to exchange my position with a chosen opponent, so that I can steal a lead.
54. As a player, I want to hold at most one Buff, with a new one replacing it, so that the screen stays simple.
55. As a player, I want held Buffs (Ward, Hex, Swap) to wait until I use them and immediate Buffs (Haste, Insight) to apply on the spot, so that each Buff behaves predictably.
56. As a player, I want to see every player's held Buff, so that I can anticipate a Hex or a Swap.
57. As a player, I want Debuffs (Retreat, lose next Turn, lose a Life) to be announced when they happen, so that I understand what hit me.
58. As a player, I want Buffs and Debuffs placed differently in every Dungeon, so that nothing is memorised between games.

### Map and visibility

59. As a player, I want my own Map showing only the Rooms I have Revealed, so that exploration is personal.
60. As a player, I want entering a Room to Reveal it and its neighbours on my Map, so that I can see where I can go next.
61. As a player, I want Revealed but unvisited Rooms to show only a silhouette, so that their contents stay a surprise.
62. As a player, I want Revealed Treasure rooms, Mimics included, to show a chest icon, so that I can choose whether to gamble.
63. As a player, I want my Map to mark the Rooms I have Visited and Cleared, so that I know where I have been.
64. As a player, I want the Map and minimap to switch to the active player's view each Turn, so that I see my own exploration.
65. As a player, I want to see where the other players are on my Map, so that I can judge the race. Only positions are shown, never their Maps.
66. As a player, I want the minimap to be a miniature of my Map, so that the two never disagree.

### Exit and winning

67. As a player, I want the Exit's Guardian to ask three Questions, one per Turn, so that the finale is tense and visible.
68. As a player, I want my Exit progress kept between Turns and after a Retreat, so that a mistake delays me without resetting me.
69. As a player, I want the first player to Clear the Exit to win immediately, so that the race has a clear end.
70. As a player, I want a results screen naming the winner and showing the Seed, so that we can rematch or share.
71. As a player, I want to restart quickly, with a new Seed or the same one, so that we can play again right away.

### Presentation and accessibility

72. As a player, I want all on-screen text in Portuguese, so that I understand the game.
73. As a player, I want the reduced-motion option to keep working, so that the game stays comfortable.
74. As a player, I want the camera, doors and walking transitions to keep working, so that the Dungeon still feels like a place.
75. As a player, I want long Questions and four players' panels to fit the minimum window, so that nothing is cut off.

### Developer

76. As a developer, I want the rules to be Tk-free and driven by a few actions, so that they can be tested without a display.
77. As a developer, I want the Dungeon (place) separate from the Expedition (play), so that the code matches the glossary.
78. As a developer, I want the question bank in its own module, so that removing the classic game does not take it with it.

## Implementation Decisions

- **Classic game removed.** The classic board game's rules, its Tk board, its terminal front-end and their launch flags are deleted. The default launch goes straight to the crawler. See ADR-0002.
- **Question bank module.** Question loading, the built-in fallback questions and answer checking move out of the classic rules into their own module. Banks are keyed by Tier (easy, medium, hard), backed by the existing three question files. Drawing a Question takes a Tier and a random source, and never repeats a Question already drawn in the same Expedition. If a Tier runs out, its pool is reset.
- **Dungeon generation.** A function takes a Seed and a Difficulty and returns a Dungeon: Room coordinates, passages, Depth of every Room, the Entrance, the Exit, and the kind of every Room. The existing orthogonal layout generator is kept, including its loop at the Entrance, its shortcuts, its guaranteed Dead End and an Exit at maximum Depth. Room kinds other than Entrance and Exit are drawn from weighted kinds (Combat, Elite, Treasure, Mimic, Trap, Sanctuary, Empty). The weights are the implementer's starting values, to be tuned by playtests, with Combat the most common. Clock rooms and point multipliers go away. The legacy `size` parameter and `floors` disappear.
- **Difficulty table** (starting values):

  | Difficulty | On-screen | easy | medium | hard | Rooms | Question time |
  |---|---|---|---|---|---|---|
  | Easy | Aventureiro | 70% | 25% | 5% | 15 | 30s |
  | Medium | Guerreiro | 40% | 45% | 15% | 22 | 22s |
  | Hard | Pesadelo | 15% | 40% | 45% | 30 | 15s |
  | Campaign | Campanha | 85% | 12% | 3% | 30 | 30s |

  Elite rooms override the mix with a hard-Tier Question. Campaign no longer progresses by Depth.
- **Seed.** A Seed is a non-negative integer, shown in a short human-friendly form. One random source derived from the Seed generates the Dungeon and its contents. Question draws use a second stream derived from the same Seed, so the Dungeon stays identical whatever happens during play. Questions are not guaranteed to repeat between two plays of a Seed. A Seed is only guaranteed within the same game version and question bank.
- **Expedition (rules).** Tk-free, built from Difficulty, player count, Seed and an injected clock (the existing pattern). It owns the Dungeon and one Player per participant. It exposes:
  - Actions: move through a door; answer the current Question; retreat; use the held Buff, with a target player for Hex and Swap; and tick, which expires an overdue Question.
  - Readable state: active player; each player's position, Lives, held Buff, Revealed, Visited and Cleared sets, Exit progress and pending skipped Turn; the current Question with its Tier and remaining time; the last event (correct, wrong with penalty, Buff gained, Debuff suffered, return to Entrance, win), with enough detail for the screen to announce it; the winner; and the Seed.
  - Actions that are invalid for the current state (wrong player, missing door, no Question, game over) return a falsy result and change nothing.
- **Player.** Per-participant state: position, the Room they came from (for Retreat), Lives (3), held Buff (at most one), Revealed, Visited and Cleared sets, Exit hits, and skip-next-Turn flag. Treasure, Trap and Mimic effects key off the player's Visited set, so each fires only on that player's first visit.
- **Turn flow.** The active player makes one move. On arrival:
  - If the Room has a Guardian the player has not Cleared, a Question starts.
  - Otherwise, any first-visit effect applies and the Turn passes.
  - A correct answer Clears the Room (an Elite room also grants a Buff) and ends the Turn. At the Exit, a correct answer adds one hit, and three hits win.
  - A wrong answer or timeout applies the Tier penalty: easy loses a Life, medium skips the next Turn, hard Retreats. A held Ward is consumed instead of the penalty.
  - Losing the last Life moves the player to the Entrance with 3 Lives.
  - Haste grants one extra move before the Turn passes.
  - A player who starts a Turn in a Room they have not Cleared either answers a new Question or Retreats.
  - The turn order skips any player flagged to skip, clearing the flag.
- **Effects.** Ward (held): cancels the next wrong-answer penalty. Haste (immediate): one extra move. Insight (immediate): Reveals Rooms within two passages. Hex (held): a chosen opponent skips their next Turn. Swap (held): exchange positions with a chosen opponent; neither player's Room states change. A newly gained held Buff replaces the current one. Debuffs are Retreat, skip next Turn and lose a Life. Effects never target the player who triggered them, except Debuffs, which hit that player.
- **Revealing.** Entering a Room Reveals it and its neighbours for that player only. The Map draws only the player's own Revealed Rooms and the passages between them. Unvisited Rooms appear as silhouettes; Treasure rooms and Mimics also show a chest icon. Opponents' positions are drawn on every Map.
- **Removed.** Score, combo, speed bonus, the global expedition clock, shared lives and the cooperative turn rotation. See ADR-0001.
- **Screen.** The current UI frame named `Expedition` is renamed `ExpeditionScreen`, freeing the name for the rules. It renders the active player's Map and minimap, the turn indicator, every player's Lives and held Buff, the Question with its Tier and timer, event announcements, the Seed, and a results screen with restart options (new Seed, same Seed). The camera, doors, walking transitions and reduced motion keep their current behaviour, rebound to the active player's position.
- **Menu.** Difficulty cards use the new on-screen names. Player selection keeps 1 to 4. An optional Seed field is added; when it is empty or invalid, a random Seed is used.
- **Text.** All on-screen strings stay Portuguese. Code identifiers follow the glossary in English.

## Testing Decisions

- Good tests drive only the public actions and read only observable state. They never reach into private fields or check how the generator builds a layout. They use a fixed Seed and an injected clock, so every run is deterministic.
- **Seam 1: Expedition rules (Tk-free).** This replaces the current dungeon rules tests. It covers:
  - Generation invariants across many Seeds and every Difficulty: connected, reciprocal orthogonal passages, at least one loop, at least one Dead End, the Exit at maximum Depth with one passage, Room counts per Difficulty.
  - Same Seed, same Dungeon.
  - Tier frequencies close to each Difficulty's mix over many draws; Elite rooms always hard-Tier.
  - No repeated Question within an Expedition.
  - Turn order, including skipped Turns.
  - Each Tier's penalty, Ward cancelling it, and the return to the Entrance at 0 Lives with Map and Cleared rooms kept.
  - Per-player Revealed, Visited and Cleared; a second player still facing a Guardian someone else Cleared.
  - First-visit-only Treasure, Trap and Mimic effects.
  - Every Buff, including Hex and Swap targeting.
  - Exit progress across Turns and Retreats; first to three hits wins; invalid actions rejected without side effects.
  - Prior art: the existing dungeon rules tests (seeded random source, injected clock, path-walking helpers).
- **Seam 2: Screen and menu (Tk display).** This adapts the existing UI and menu tests. It covers:
  - The Map and minimap showing only the active player's Revealed Rooms and switching each Turn.
  - Opponents' positions drawn.
  - The Seed shown, and typing a Seed in the menu starting that Dungeon.
  - The turn indicator, Lives and held Buff for four players fitting the minimum window.
  - The existing portal, camera, transition, reduced-motion and callback-cancellation tests rebased onto Turns.
  - Prior art: the existing dungeon UI and menu tests.
- No separate seam for the question bank: Tier selection and no-repeat draws are observed through the Expedition.
- Tests of the removed classic game are deleted along with it.

## Out of Scope

- Online or networked multiplayer, including separate Dungeons per player.
- Translations into English or Spanish; only the strings stay localisable in spirit.
- Special modes: dice movement, turn limits, Campaign variants and other rule variants.
- Pacing tuning beyond the starting values in the Difficulty table and the Room-kind weights; that comes from playtests.
- Persistent progression between Expeditions: history, profiles, unlocks.
- Sound.
- Reviewing or translating the question bank's content.

## Further Notes

- Vocabulary follows CONTEXT.md; this spec carries out ADR-0001 (competitive race) and ADR-0002 (crawler replaces the classic game).
- The round notes in DESIGN.md and the README's feature list describe the cooperative game and the classic board; both need rewriting as part of this work.
- Uncommitted work exists in the screen, room scene and motion modules; commit it before starting, because this spec rewrites those areas.
- Suggested order for tickets: question bank extraction and classic removal, then Dungeon generation with Seed and Room kinds, then Expedition rules, then the screen and menu, then docs.
