# Python-Minigame

## A Masmorra dos Ecos — novo modo gráfico

Execute `python gui.py` ou `python __main__.py --gui` (Python 3.10+ com Tkinter).
No Windows, dê dois cliques em `jogar.cmd`; ele usa o Python integrado ao Codex
quando disponível, ou o comando `python` do sistema.
Uma expedição de quiz em um complexo de salas em perspectiva. A câmera começa
olhando para o norte; use **Olhar** ou **Alt + Q/E** para girar 90 graus.
Use as portas, os botões, **Alt + setas** ou clique em uma sala vizinha no minimapa.
As setas movem em relação à câmera; os botões informam a direção geográfica e a
seta do minimapa mostra a orientação atual. Olhar não apaga a resposta digitada.
Digite a resposta e pressione Enter. O banco de perguntas atual está em inglês.

O menu tem arte original do núcleo da masmorra, partículas e grafismos animados,
cartões de dificuldade e seleção de equipe de 1 a 4 jogadores. A opção de efeitos
também controla as animações do menu. A arte é carregada de `assets/` sem rede ou
dependências adicionais; caso esteja ausente, o menu usa um desenho procedural.

- **Masmorra geográfica procedural:** 26 / 35 / 44 / 53 salas por modo, distribuídas
  em coordenadas reais. Cada partida tem bifurcações, ciclos, atalhos e becos.
  Há de uma a quatro passagens por sala; paredes nunca funcionam como portas.
- **Exploração:** o minimapa revela a sala atual e suas vizinhas, desenhando apenas
  passagens descobertas. Salas concluídas ficam preenchidas. O núcleo final é
  uma sala terminal; os demais ramos podem ser explorados antes de entrar nele.
- **Quiz e feedback:** corredores tecnológicos, terminais e acentos em ciano;
  pergunta em destaque, pontos flutuantes, partículas e combo. Desative os efeitos
  para movimento reduzido.
- **Salas e movimento:** concreto com textura procedural, piso em perspectiva,
  portas metálicas com batentes e abertura animada. A caminhada começa após abrir
  a porta; o desafio da próxima sala começa na chegada. Olhar e andar consomem
  o relógio da expedição. Com efeitos desativados, os movimentos são imediatos.
- **Relógio contínuo:** explorar e escolher também consome tempo. Explorador:
  240s / 30s por pergunta; Aventureiro: 190s / 22s; Pesadelo: 145s / 15s.
  A Campanha tem 300s e perguntas progressivas de 30s, 22s e 15s, conforme a
  distância por portas desde a entrada.
- **Risco e recompensa:** caches dão ×1,5 pontos; sobrecargas dão ×2 com 25%
  menos tempo; recuperação restaura uma vida; sincronizadores acrescentam 12s.
- **5 vidas:** erro ou tempo esgotado da pergunta custa uma vida e quebra o combo.
  O relógio geral zerado encerra a partida. Cada sala exige um acerto; o núcleo,
  três. Após um erro, a resposta aparece por 3s antes de uma nova pergunta.
- **Pontuação:** base de 1.000 + até 1.000 por velocidade, multiplicada pelo combo
  (até ×3,25) e pela sala.
- **Solo ou cooperação local para até 4:** tempo, vidas e combo compartilhados;
  os jogadores se alternam a cada resposta, com pontuações individuais.
- **Voltar e explorar:** qualquer passagem pode ser percorrida nos dois sentidos
  após resolver o desafio. “Voltar pelo trajeto” desfaz o último deslocamento;
  esse comando é diferente da direção sul. Revisitar não repete recompensas.

O tabuleiro gráfico anterior continua disponível em `python gui.py --board`;
`python __main__.py` mantém o modo clássico de terminal descrito abaixo.

A geração espacial fica em `dungeon_map.py`, as regras em `dungeon.py` e a interface
em `dungeon_ui.py`; o menu fica em `menu_ui.py` e a cena das salas em `room_scene.py`.
Rode `python -m unittest -v test_dungeon test_dungeon_ui test_menu_ui` para
validar regras e integração (os testes de interface precisam de um display Tk).
O gerador recebe um `random.Random(seed)` para testes reproduzíveis.

Esta é a primeira rodada da evolução do crawler. A análise individual das sete
imagens e as próximas etapas estão em [DESIGN.md](DESIGN.md). O balanceamento dos
relógios frente às diferentes distâncias dos mapas ainda precisa de playtests.

## Modo clássico

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
⇄	Swap	Switch places with another player, then move on.
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

    Make sure you have Python 3.10+ (Tkinter ships with the standard installer).

    Keep the question files next to the game:

        easy_questions.json

        medium_questions.json

        hard_questions.json

🖥️ Two ways to play

    Graphical board (default choice for a couch game):

        python gui.py --board

    A window opens with the whole board drawn as a winding path of coloured
    tiles: pick players and difficulty, hit Roll dice, type your answer, and
    watch your pawn walk the board. Forks and targeting powers pop up as
    dialogs, the sidebar tracks every player's progress, and hovering a tile
    tells you what it does.

    Classic terminal board:

        python __main__.py

    The original ASCII experience. `python __main__.py --gui` opens the new
    dungeon crawler; add `--board` for the classic graphical board.

🧱 Project layout

    core.py       - rules, board generation, tile effects, turn engine (no I/O)
    gui.py        - Tkinter board, dice, pawns and dialogs
    __main__.py   - terminal front-end
    *_questions.json - the trivia banks

    Both front-ends drive the same rules in core.py, so a change to the game
    shows up in each of them.

💡 Tips for Adventurers

    Mystery tiles are wild cards. Don’t get too comfortable.

    Quiz Boost doubles your move — answer wisely.

    Campaign Mode is long, unpredictable, and full of surprises.

    Alliances may form… but betrayal is just one tile away.

🏁 Goal

Be the first to reach the final tile. But beware: the board is alive, and it plays dirty.
