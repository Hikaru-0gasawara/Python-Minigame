# Python-Minigame

🐍✨ Python Trivia Adventure

A chaotic campaign of dice, questions, and unpredictable powers.

Welcome, traveler! You’ve just opened the gateway to a trivia-powered board game where knowledge is your sword, luck is your shield, and the board itself is alive with mischief. Whether you’re playing solo or with friends, this game will test your wits, your strategy, and your ability to survive the chaos.
🎮 How It Works

    🎲 Roll the dice → Each turn begins with a roll.

    📚 Answer a trivia question → Correct = move forward, Wrong = stay put.

    🗺️ Navigate a procedural board → Every game creates a brand-new map with surprises.

        The path bends with curves (indentation) so it looks alive.

        In Campaign Mode, you’ll encounter branches where you must choose Path A or Path B.

🧩 Tile Types
Symbol	Tile Type	Effect
.	Normal	Just a regular tile. Nothing fancy.
+	Bonus	Move extra spaces. Yay!
-	Trap	Lose spaces. Boo!
?	Mystery	Could be amazing… or terrible.
*	Quiz Boost	Double your move if you answer correctly.
⇄	Swap	Switch places with another player.
↓	Push Down	Choose someone to send backward.
↑	Lift Up	Choose someone to boost forward.
✦	Teleport	Warp to a random tile.
⏭	Skip Turn	Miss your next turn.
✪	Double Trouble	Double your roll.
⚔	Steal	Take another player’s roll. Sneaky!
🧠 Difficulty Levels

Choose your challenge:

    🌱 Easy — 36 spaces, friendly board

    ⚖️ Medium — 46 spaces, balanced board

    💀 Hard — 56 spaces, punishing board

    🔥 Campaign Mode — 123 spaces, progressive difficulty, reshuffling chaos, curves + branches

🔥 Campaign Mode: The Ultimate Quest

    Starts with easy questions, shifts to medium, ends with hardcore trivia.

    The board reshuffles at 1/3, 2/3, and the final stretch.

    Includes 3–4 forks where you must choose:

        Path A → safer, more bonuses/lift ups.

        Path B → riskier, more traps/steals/mysteries.

    All powers are active. Expect betrayal, teleportation, and unexpected boosts.

    Only the bold survive.

👥 Multiplayer Mayhem

    Up to 4 players.

    Some powers let you choose who to target.

    Invalid choices? The game picks randomly — chaos never sleeps.

🧠 Trivia Questions

    Questions are loaded from:

        easy_questions.json

        medium_questions.json

        hard_questions.json

    If files are missing, built-in questions keep the game alive.

🚀 How to Run

    Make sure you have Python 3.10+.

    Place your question files in the same folder as the game:

        easy_questions.json

        medium_questions.json

        hard_questions.json

        Run the game:
        bash
            python __main__.py

        Choose your difficulty and number of players.
        
        Let the chaos begin!
    
💡 Tips for Adventurers

    Mystery tiles are wild cards. Don’t get too comfortable.

    Quiz Boost doubles your move — answer wisely.

    Campaign Mode is long, unpredictable, and full of surprises.

    Alliances may form… but betrayal is just one tile away.

🏁 Goal

Be the first to reach the final tile. But beware: the board is alive, and it plays dirty.
