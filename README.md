# Python-Minigame

## A Masmorra dos Ecos — novo modo gráfico

Execute `python .` ou `python dungeon_ui.py` (Python 3.10+ com Tkinter).
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
  Cada jogador tem uma cor fixa e um cartão no placar. O indicador “NO CONTROLE”,
  o contorno do quiz e o botão de resposta identificam a vez atual; o feedback
  informa quem respondeu. A resposta anterior é limpa ao trocar a vez.
- **Transições refinadas:** folhas rígidas deslizam atrás dos batentes; câmera
  com aceleração suave e balanço reduzido, escurecimento breve entre vistas e
  chegada suave. A porta sob o cursor recebe destaque. Todos esses movimentos
  respeitam a opção de efeitos, incluindo o aviso animado de troca de jogador.
- **Voltar e explorar:** qualquer passagem pode ser percorrida nos dois sentidos
  após resolver o desafio. “Voltar pelo trajeto” desfaz o último deslocamento;
  esse comando é diferente da direção sul. Revisitar não repete recompensas.

O banco de perguntas fica em `questions.py`, a geração espacial em `dungeon_map.py`, as regras em `dungeon.py` e a interface
em `dungeon_ui.py`; o menu fica em `menu_ui.py` e a cena das salas em `room_scene.py`.
Rode `python -m unittest -v test_questions test_dungeon test_dungeon_ui test_menu_ui` para
validar regras e integração (os testes de interface precisam de um display Tk).
O gerador recebe um `random.Random(seed)` para testes reproduzíveis.

Esta é a primeira rodada da evolução do crawler. A análise individual das sete
imagens e as próximas etapas estão em [DESIGN.md](DESIGN.md). O balanceamento dos
relógios frente às diferentes distâncias dos mapas ainda precisa de playtests.
