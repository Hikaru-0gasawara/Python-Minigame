# Python-Minigame

## ECOS · A Masmorra dos Ecos

Uma corrida de quiz por dentro de um computador gigante que está morrendo. Ele
abriga ECO, uma IA que transforma cada passagem numa prova. A cada expedição nasce
uma masmorra nova. De 1 a 4 jogadores dividem a mesma tela e a mesma masmorra,
mas cada um por si: o primeiro a escapar pelo núcleo vence.

Execute `python .` ou `python dungeon_ui.py` (Python 3.10+ com Tkinter, sem
outras dependências). No Windows, dê dois cliques em `jogar.cmd`; ele usa o
Python integrado ao Codex quando disponível, ou o comando `python` do sistema.
O banco de perguntas atual está em inglês.

### O visual

Tudo é pixel art desenhada pelo próprio código numa tela de 320×200, com uma
paleta fixa de 32 cores, e ampliada pelo maior fator inteiro que cabe na janela.
Quando o formato da janela não bate, sobram faixas pretas, e o pixel nunca é
esticado. Não há arquivos de imagem: salas, objetos, fonte e menu são montados na
abertura do jogo.

ECO fala pelos **guardiões**, estátuas encapuzadas com uma tela no rosto. O
horror é sugerido, nunca explícito. A profundidade da sala define o **setor**,
mostrado no canto superior esquerdo:

| Setor | Aparência | Porta |
|---|---|---|
| Raso | Concreto frio, tubos ciano | Comporta deslizante |
| Meio | Ferrugem, luz âmbar | Persiana de aço enferrujada |
| Fundo | Vermelho de alarme | Porta de cofre |

Ao atravessar uma porta, ela se abre quadro a quadro e a câmera avança pelo vão
em saltos de zoom. A sala seguinte chega no escuro, os tubos piscam até acender e
o guardião desperta.

### Como se joga

- **Turnos:** os jogadores jogam em ordem fixa (J1, J2, …). Cada turno é **um
  movimento** para uma sala vizinha, mais o que essa sala exigir.
- **Guardiões:** ao entrar numa sala com guardião, ECO fala numa caixa de
  diálogo. Primeiro vem uma provocação, depois a pergunta, letra por letra e com
  um bipe de voz. **Enter** ou um clique mostram tudo de uma vez, e o tempo da
  pergunta só começa quando ela aparece inteira. A caixa mostra o nível da
  pergunta e quanto custa errar (ou “ESCUDO ANULA”).
- Cada guardião pergunta a **todo** jogador que entra, mesmo que outro já o
  tenha vencido, e nenhuma pergunta se repete na mesma expedição. Acertar libera a
  sala para você e o guardião sai do caminho, com o olho verde. Numa sala ainda
  não liberada, use o turno para responder de novo ou para **recuar pelo
  trajeto**.
- **Erros custam conforme o nível da pergunta** (errar o fácil dói mais):

  | Pergunta | Ao errar ou estourar o tempo |
  |---|---|
  | Fácil | −1 vida |
  | Média | perde a próxima vez |
  | Difícil | recua uma sala |

- **Vidas:** cada jogador tem 3. Sem vidas, volta à entrada com as 3 vidas de
  volta, mantendo o mapa e as salas já liberadas.
- **Núcleo (saída):** o guardião do núcleo faz 3 perguntas, uma por turno, e
  cada acerto acende uma das três travas do portão. O progresso fica guardado
  mesmo se você sair ou recuar. Quem completar primeiro vence.

### Dificuldades

| Dificuldade | Salas | Tempo por pergunta | Fácil / Média / Difícil |
|---|---|---|---|
| Aventureiro | 15 | 30s | 70% / 25% / 5% |
| Guerreiro | 22 | 22s | 40% / 45% / 15% |
| Pesadelo | 30 | 15s | 15% / 40% / 45% |
| Campanha | 30 | 30s | 85% / 12% / 3% |

A Campanha é o modo de exploração: masmorra grande, perguntas quase sempre
fáceis. Os valores são um ponto de partida para playtests.

### Salas

| Sala | Na cena | Efeito |
|---|---|---|
| Guardião | Estátua de ECO | Uma pergunta para passar |
| Elite | Estátua maior, blindada, com o emblema de ECO | Pergunta sempre difícil; quem vence ganha um poder |
| Tesouro | Contêiner de dados blindado | Um poder na sua primeira visita |
| Mímico | Igual ao tesouro, até mostrar as mandíbulas | Uma penalidade na sua primeira visita |
| Armadilha | Placas de pressão e emissores na parede | Uma penalidade na sua primeira visita |
| Santuário | Cápsula de reparo com luz verde | +1 vida a cada visita, até 3 |
| Sala vazia | Racks de servidor caídos, cabos e poças | Nada |
| Entrada | O elevador por onde vocês desceram | Ponto de partida |
| Núcleo | Portão com três travas | A saída: 3 acertos |

Cada sala mostra o que **você** sabe e fez nela: o baú que você abriu, a
armadilha que já disparou para você, o guardião que você venceu. Salas com uma
só passagem, fora do caminho até o núcleo, podem guardar qualquer tipo de sala.

### Poderes

- **Pressa** (imediato): mais um movimento neste turno.
- **Visão** (imediato): revela as salas a até dois passos.
- **Escudo** (guardado): anula a penalidade do seu próximo erro. Não protege
  contra armadilhas, mímicos nem maldições.
- **Maldição** (guardado): um rival à sua escolha perde a próxima vez.
- **Troca** (guardado): troca de lugar com um rival à sua escolha.

Cada jogador guarda um poder por vez; pegar outro substitui o atual. Maldição e
Troca são usadas no cartão do jogador da vez, clicando no rival (J2, J3…) ou com
**Alt + número do rival**, e não gastam o turno.

### A tela e os controles

A janela inteira é a masmorra. No canto superior esquerdo ficam o jogador da vez,
a sala, o setor e para onde ele olha. No canto superior direito fica o **mapa**
do jogador da vez, com a seed. Embaixo ficam os cartões dos jogadores, e o da
vez é maior e traz as ações.

- **Mover:** clique numa porta da cena (passar o mouse diz o que há atrás dela),
  na aba “↓ … · ATRÁS” no alto da tela para a porta às suas costas, numa sala
  vizinha no mapa, ou use **Alt + setas** (esquerda, frente, direita, trás).
- **Olhar:** as setas ← → nas bordas da tela ou **Alt + Q/E** giram a câmera 90
  graus; cada jogador mantém a sua direção entre os turnos.
- **Recuar:** “↶ RECUAR” no cartão ou **Alt + R**.
- **Responder:** é só digitar (Backspace apaga) e pressionar **Enter**.
- **Som:** “SOM ●/○”, embaixo do mapa, ou **Alt + M**.
- **Esc** volta ao menu.

O mapa é só seu: mostra o que você descobriu, troca a cada turno e marca a
posição de todos os rivais. Salas ainda não visitadas aparecem como silhuetas
pontilhadas; baús aparecem em âmbar, e nem todo baú é o que parece.

### Menu

O menu é uma cena animada: torres de servidores em paralaxe, o núcleo pulsante de
ECO, cabos soltando faíscas e uma falha de imagem de vez em quando. A coluna da
esquerda tem **Dificuldade**, **Jogadores**, **Seed**, **Som**, **Movimento** e
**ENTRAR**:

- **↑ ↓** ou **Tab** escolhem a linha, **← →** mudam o valor, **Enter** ou
  **espaço** confirmam. O mouse também funciona.
- Na linha da seed, digite números e letras de A a F (e `-`).
- **F1** abre o “Como jogar”.
- **Movimento: reduzido** troca portas, zoom, desvanecimentos, diálogo letra por
  letra, partículas e a animação do menu por cortes imediatos.

No canto inferior direito ficam os **recordes** da dificuldade escolhida.

### Seeds

Toda expedição nasce de uma seed, mostrada no mapa e na tela final (por exemplo
`3F9A-12C0`). Digite uma seed no menu para jogar exatamente a mesma masmorra,
com as mesmas salas e os mesmos poderes nos mesmos lugares; deixe o campo vazio
para uma masmorra nova. As perguntas sorteadas podem variar entre duas expedições
com a mesma seed, e a seed só é garantida na mesma versão do jogo.

### Resultado e recordes

A tela final mostra quem escapou, na cor do jogador, além da dificuldade, da
seed, do tempo e de uma linha por jogador. Ela oferece **Revanche · mesma seed**,
**Nova seed** e **Menu**: setas ou Tab escolhem, Enter ou espaço confirmam, e
Esc volta ao menu.

O tempo vai do início da expedição até a fuga. Os cinco melhores de cada
dificuldade ficam salvos como **recordes**, com seed, número de jogadores e data,
em `%APPDATA%\ECOS\records.json` (fora do Windows, em `~/.local/share/ECOS`). A
tela avisa quando a fuga entra na lista (“★ NOVO RECORDE · #2”). Um arquivo
ausente ou corrompido vale como placar vazio e nunca impede o jogo de abrir.

### Som

Bipes de voz, porta, baú, armadilha, acerto e erro. Os sons são gerados pelo
código na abertura do jogo, guardados numa pasta temporária e tocados pelo som
padrão do Windows; um som novo corta o anterior. Em outros sistemas, o jogo roda
em silêncio. O mudo fica no menu, no HUD (“SOM”) e em **Alt + M**.

## Para desenvolvedores

| Módulo | Papel |
|---|---|
| `questions.py` | Banco de perguntas por nível, sem repetição na expedição |
| `dungeon_map.py` | Planta ortogonal com bifurcações, ciclos e salas sem saída |
| `dungeon.py` | Regras sem Tk: geração por seed, turnos, guardiões, poderes, tempo da expedição |
| `scene.py` | O que cada jogador vê numa sala, sem Tk: setor, portas, guardião, objeto, decoração |
| `palette.py`, `pixels.py` | As 32 cores, rampas e pontilhado; a tela indexada e a codificação PNG |
| `font.py` | Fonte bitmap e quebra de linha |
| `room_art.py`, `props.py` | Paredes, portas e guardiões; objetos de cada sala e decorações |
| `pixel_view.py` | Composição no Tk e ampliação inteira |
| `hud.py` | Mapa, cartões, caixa de diálogo e painel de resultado, em pixels |
| `dialogue.py` | Ritmo das falas, letra por letra |
| `audio.py` | Sons sintetizados e mudo |
| `records.py` | Recordes por dificuldade |
| `dungeon_ui.py` | Tela da expedição e tela de resultado |
| `menu_ui.py`, `menu_art.py` | Menu animado e suas camadas |
| `motion.py` | Curvas de animação |

Rode os testes com:

```bash
python -m unittest -v
```

Os testes de interface (`test_dungeon_ui`, `test_menu_ui`) precisam de um display
Tk; os demais rodam sem tela. O vocabulário do domínio (Dungeon, Expedition,
Guardian, Tier, Buff…) está em [CONTEXT.md](CONTEXT.md), e as decisões de
arquitetura em [docs/adr/](docs/adr/). O histórico de design e as próximas rodadas
estão em [DESIGN.md](DESIGN.md).
