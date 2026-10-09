# Python-Minigame

## A Masmorra dos Ecos

Uma corrida de quiz por uma masmorra gerada a cada partida. De 1 a 4 jogadores
dividem a mesma tela e a mesma masmorra, mas cada um por si: o primeiro a
escapar pelo núcleo vence.

Execute `python .` ou `python dungeon_ui.py` (Python 3.10+ com Tkinter, sem
outras dependências). No Windows, dê dois cliques em `jogar.cmd`; ele usa o
Python integrado ao Codex quando disponível, ou o comando `python` do sistema.
O banco de perguntas atual está em inglês.

### Como se joga

- **Turnos:** os jogadores jogam em ordem fixa (J1, J2, …). Cada turno é **um
  movimento** para uma sala vizinha, mais o que essa sala exigir.
- **Guardiões:** ao entrar numa sala com guardião, você responde a uma pergunta
  no mesmo turno. Cada guardião pergunta a **todo** jogador que entra, mesmo que
  outro já o tenha vencido, e nenhuma pergunta se repete na mesma partida.
  Acertar libera a sala para você. Numa sala ainda não liberada, use o turno para
  responder de novo ou para **recuar pelo trajeto**.
- **Erros custam conforme o nível da pergunta** (errar o fácil dói mais):

  | Pergunta | Ao errar ou estourar o tempo |
  |---|---|
  | Fácil | −1 vida |
  | Média | perde a próxima vez |
  | Difícil | recua uma sala |

- **Vidas:** cada jogador tem 3. Sem vidas, volta à entrada com as 3 vidas de
  volta, mantendo o mapa e as salas já liberadas.
- **Núcleo (saída):** o guardião do núcleo faz 3 perguntas, uma por turno. O
  progresso fica guardado mesmo se você sair ou recuar. Quem completar primeiro
  vence.

### Dificuldades

| Modo | Salas | Tempo por pergunta | Fácil / Média / Difícil |
|---|---|---|---|
| Aventureiro | 15 | 30s | 70% / 25% / 5% |
| Guerreiro | 22 | 22s | 40% / 45% / 15% |
| Pesadelo | 30 | 15s | 15% / 40% / 45% |
| Campanha | 30 | 30s | 85% / 12% / 3% |

A Campanha é o modo de exploração: masmorra grande, perguntas quase sempre
fáceis. Os valores são um ponto de partida para playtests.

### Salas

Antes de entrar, uma sala aparece no mapa só como silhueta tracejada; apenas
baús ficam visíveis (`$`), e nem todo baú é o que parece.

| Sala | Símbolo | Efeito |
|---|---|---|
| Guardião | G | Uma pergunta para passar |
| Elite | ! | Pergunta sempre difícil; quem vence ganha um poder |
| Tesouro | $ | Um poder na sua primeira visita |
| Mímico | $ → M | Parece um tesouro; na primeira visita, uma penalidade |
| Armadilha | ^ | Uma penalidade na sua primeira visita |
| Santuário | + | +1 vida a cada visita, até 3 |
| Sala vazia | · | Nada |
| Núcleo | X | A saída: 3 acertos |

Becos sem saída existem e podem guardar qualquer tipo de sala.

### Poderes

- **Pressa** (imediato): mais um movimento neste turno.
- **Visão** (imediato): revela as salas a até dois passos.
- **Escudo** (guardado): anula a penalidade do seu próximo erro. Não protege
  contra armadilhas, mímicos nem maldições.
- **Maldição** (guardado): um rival à sua escolha perde a próxima vez.
- **Troca** (guardado): troca de lugar com um rival à sua escolha.

Cada jogador guarda um poder por vez; pegar outro substitui o atual. Maldição e
Troca são usadas no painel lateral (“USAR EM: J2 / J3 …”) e não gastam o turno.

### Mapa e controles

- Cada jogador tem o **próprio mapa**, com apenas o que ele descobriu; o mapa
  troca a cada turno e mostra a posição de todos os rivais.
- Mova-se pelas portas da cena, pelos botões de direção, por **Alt + setas** ou
  clicando numa sala vizinha no mapa. **Olhar** ou **Alt + Q/E** gira a câmera
  90 graus; cada jogador mantém a sua direção entre os turnos.
- Digite a resposta e pressione **Enter**.
- “Efeitos animados” liga ou desliga portas animadas, caminhada, partículas e
  avisos de turno; desligado, os movimentos são imediatos.

### Seeds

Toda partida nasce de uma seed, mostrada no mapa e na tela final (por exemplo
`3F9A-12C0`). Digite uma seed no menu para jogar exatamente a mesma masmorra,
com as mesmas salas e os mesmos poderes nos mesmos lugares; deixe o campo vazio
para uma masmorra nova. As perguntas sorteadas podem variar entre duas partidas
com a mesma seed, e a seed só é garantida na mesma versão do jogo.

Ao fim, a tela de resultado mostra o vencedor e a seed, com **Revanche · mesma
seed**, **Nova seed** e **Menu**.

## Para desenvolvedores

| Módulo | Papel |
|---|---|
| `questions.py` | Banco de perguntas por nível, sem repetição na partida |
| `dungeon_map.py` | Planta ortogonal com bifurcações, ciclos e becos |
| `dungeon.py` | Regras sem Tk: geração por seed, turnos, guardiões, poderes |
| `dungeon_ui.py` | Tela da partida e tela de resultado |
| `menu_ui.py` | Menu ilustrado |
| `room_scene.py`, `motion.py` | Cena das salas em perspectiva e animações |

Rode os testes com:

```bash
python -m unittest -v test_questions test_dungeon test_dungeon_ui test_menu_ui
```

Os testes de interface precisam de um display Tk. O vocabulário do domínio
(Dungeon, Expedition, Guardian, Tier, Buff…) está em [CONTEXT.md](CONTEXT.md), e
as decisões de arquitetura em [docs/adr/](docs/adr/). O histórico de design e as
próximas rodadas estão em [DESIGN.md](DESIGN.md).
