# Records are stored locally, outside the repository

Until now nothing survived an Expedition. The menu's scoreboard needs Records, so we keep the five best escape times per Difficulty (time from the start of the Expedition to the winner's escape, Seed, player count and date) in a JSON file in the user's data folder (`%APPDATA%` on Windows), never in the repository. There are no accounts, names or network: the race is hot-seat, so players stay J1 to J4. A missing or unreadable file means an empty scoreboard, never a crash or a lost game.
