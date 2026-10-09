# Direção do quiz crawler

Este documento registra a direção do jogo e um roteiro para evoluí-lo parte por
parte. As etapas futuras são propostas; sua presença aqui não significa que já
foram implementadas. As rodadas 1 a 3 descrevem o crawler cooperativo, com
pontuação, combo e relógio compartilhados; a rodada 4 o transformou numa corrida
competitiva (ver [ADR-0001](docs/adr/0001-competitive-race.md)) e removeu o
tabuleiro clássico ([ADR-0002](docs/adr/0002-crawler-is-the-whole-game.md)).
O vocabulário do domínio está em [CONTEXT.md](CONTEXT.md).

## Leitura das sete imagens

1. **Corredor de pedra, inventário à esquerda e retratos à direita.** A janela
   central dá profundidade ao espaço; o mapa pequeno mantém a orientação sem
   interromper a exploração. Aproveitar essa composição e a sensação de estar
   dentro de uma sala. Traduzir objetos e personagens fantásticos para recursos,
   desafios e identidade dos participantes do nosso quiz.
2. **Arco de pedra aberto para uma floresta.** A organização da interface se
   mantém enquanto o ambiente muda. Isso sugere setores visualmente distintos
   usando os mesmos controles. O registro de eventos abaixo da cena também é
   útil para mostrar o último acerto, recompensa ou penalidade.
3. **Sala em primeira pessoa com criatura e inventário sobreposto.** A cena
   domina a imagem, comunicando presença e ameaça. Aproveitar perspectiva,
   iluminação e escala; evitar que painéis encubram a pergunta. Um terminal ou
   núcleo de desafio pode ocupar o papel visual do inimigo sem exigir fantasia.
4. **Corredor central com barras, habilidades e setas nas laterais.** Os controles
   grandes tornam a navegação explícita, mas a quantidade de ícones disputa
   atenção com o centro. Usar poucas ações, vidas e tempo legíveis, e portas
   identificadas de acordo com a geografia real do mapa.
5. **Identidade Math-Havoc com números em ciano sobre preto.** O contraste,
   título inclinado e linhas radiais comunicam velocidade. Aproveitar contraste
   e acentos luminosos na nossa identidade; reservar efeitos intensos para
   momentos curtos, sem copiar título, logotipo ou composição promocional.
6. **Quiz Math-Havoc com pergunta central, tempo e estatísticas.** A pergunta e
   a entrada são o centro da interação. O relógio tem leitura visual imediata;
   pontos e sequência oferecem retorno mensurável. Manter essa hierarquia no
   crawler, com pergunta ampla, resposta por teclado e recompensa clara.
7. **Quiz minimalista em uma captura de vídeo promocional.** Os poucos elementos
   e o alto contraste favorecem a leitura rápida. Os números grandes sugerem
   feedback visual pontual. Textos de wishlist, lançamento e legendas pertencem
   à captura de referência e não são requisitos ou informações sobre nosso jogo.

## Identidade e interação

Uma expedição por um complexo de desafios de conhecimento: arquitetura escura,
portas iluminadas, painéis de dados e ciano como cor de orientação. A masmorra
continua sendo um lugar explorável; a pergunta é a ação principal de cada sala.
Verde pode indicar conclusão, âmbar uma oportunidade e vermelho um risco, sempre
acompanhados de texto ou símbolos para não depender somente de cores.

O ciclo é explorar, escolher uma rota, enfrentar o guardião, receber feedback e
decidir o próximo destino, numa corrida: cada jogador tem o próprio mapa, as
próprias vidas e o próprio poder guardado, e o primeiro a escapar vence. Os
cartões dos participantes identificam o jogador da vez, suas vidas, seu
progresso no núcleo e seu poder, sem painéis vazios de inventário.

A intensidade vem de respostas rápidas da interface: confirmação de acerto,
pontuação visível e animações curtas. A pergunta e o campo de resposta precisam
continuar legíveis durante os efeitos. A opção de movimento reduzido permanece
parte da experiência.

Os nomes Doom, Path of Exile, The Binding of Isaac, Megabonk, Vampire Survivors,
Vampire Crawlers, Dungeon Crawl e Math-Havoc foram indicados pelo usuário como
referências de intenção. Não constituem uma lista de sistemas a copiar. Nesta
rodada, a tradução prática é presença espacial, rotas diversas, ritmo e feedback
forte; sistemas adicionais devem entrar em etapas próprias.

## Rodada 1: geografia da masmorra e hierarquia visual

Substituir o grafo de três faixas por uma planta de salas em coordenadas `(x, y)`.
Conexões correspondem a passagens entre vizinhos ortogonais. A distribuição pode
crescer em diferentes direções, com bifurcações, reencontros, ciclos e becos sem
saída. A aleatoriedade deve respeitar regras de conectividade e tamanho para que
a expedição sempre seja jogável.

O minimapa representa a mesma geografia usada na navegação, com revelação
progressiva, distinção entre sala atual, visitada e concluída, e conexões reais.
O jogador pode revisitar áreas concluídas e explorar ramos opcionais sem repetir
recompensas. A distância por caminhos desde a entrada é uma referência melhor
para progressão do que a antiga coluna de profundidade.

O destino final deve ser alcançável. Voltar de um beco precisa ser possível; a
interface não pode confundir uma direção da tela com uma passagem inexistente.
Na apresentação, aumentar a presença do quiz e aproximar corredores, portas e
painéis da estética tecnológica das referências.

Critérios de validação desta rodada:

- Diferentes sementes produzem plantas distintas e conectadas.
- Passagens são recíprocas, ligam salas adjacentes e não se cruzam arbitrariamente.
- Existem escolhas espaciais reais, ramos opcionais e caminhos que se reencontram.
- O desafio final permanece acessível e a revelação não entrega o mapa inteiro.
- Revisitar salas não duplica recompensas nem gera perguntas já concluídas.
- Tempo, erros, combo e cooperação local continuam funcionando.
- Perguntas longas e o mapa continuam legíveis na janela mínima suportada.

## Rodada 2: menu ilustrado

O menu passa a apresentar a identidade de ECOS com uma ilustração original de um
núcleo de dados e corredores subterrâneos, em vez de concentrar toda a tela em um
formulário. A arte ocupa uma área própria; a configuração da expedição permanece
separada, com cartões de dificuldade, seleção rápida de equipe e uma ação de
entrada em destaque. Os textos são desenhados pela interface, não incorporados
na imagem.

Partículas e grafismos leves dão movimento ao cenário. O controle de efeitos
desliga também o movimento do menu, e sair da tela cancela seus callbacks.
A imagem acompanha o projeto, sem dependências de rede; um desenho procedural
mantém a tela funcional caso o arquivo não esteja disponível. Origem e prompt
da arte estão registrados em `assets/README.md`.

## Rodada 3: materiais, portas e câmera

As salas usam um renderizador próprio em `room_scene.py`, com concreto, fissuras,
placas e desgaste procedurais estáveis para cada sala. Portas metálicas possuem
batentes, painéis, maçanetas e trilhos, abrindo uma vista do corredor antes da
passagem. São desenhos em perspectiva no Canvas, sem dependências adicionais.

A câmera pode girar em quatro orientações. Botões de direção, portas e seta do
minimapa acompanham esse giro. Uma transição encadeia abertura e caminhada;
o desafio seguinte começa somente na chegada. O relógio geral continua correndo,
ações duplicadas ficam bloqueadas durante o deslocamento e o fim da partida
cancela a transição. Olhar mantém a pergunta e o texto digitado. Movimento reduzido
torna a navegação imediata.

## Rodada 4: corrida competitiva

O crawler virou o jogo inteiro e deixou de ser cooperativo. De 1 a 4 jogadores
correm pela mesma masmorra, um movimento por turno, em ordem fixa. Pontuação,
combo, bônus de velocidade, relógio geral e vidas compartilhadas saíram; cada
pergunta mantém seu próprio tempo, e estourá-lo conta como erro.

- **Seeds:** cada masmorra nasce de uma seed visível e digitável. A mesma seed e
  dificuldade geram a mesma planta, os mesmos tipos de sala e os mesmos efeitos;
  as perguntas usam um sorteio separado para que jogar não altere a masmorra.
- **Dificuldades:** Aventureiro, Guerreiro, Pesadelo e Campanha definem o tamanho
  (15 / 22 / 30 / 30 salas), o tempo por pergunta e a proporção de perguntas
  fáceis, médias e difíceis. A Campanha é grande e quase toda fácil.
- **Guardiões e penalidades:** todo jogador que entra enfrenta o guardião da sala;
  o estado de sala liberada é pessoal. Errar uma fácil custa uma vida, uma média
  custa a próxima vez e uma difícil faz recuar. Sem vidas, o jogador volta à
  entrada com as vidas restauradas e o mapa preservado.
- **Salas e poderes:** elite, tesouro, mímico, armadilha, santuário e sala vazia,
  sorteados pela seed. Pressa e Visão agem na hora; Escudo, Maldição e Troca
  ficam guardados, um por vez, e os dois últimos atingem um rival.
- **Mapa por jogador:** cada um vê só o que descobriu; salas não visitadas são
  silhuetas, exceto baús, que podem esconder mímicos. Os rivais aparecem como
  pontos.
- **Resultado:** o núcleo pede 3 acertos, um por turno. A tela final mostra o
  vencedor e a seed e oferece revanche na mesma seed ou uma seed nova.

Decisões em aberto após esta rodada: recuar com a pergunta na tela custa apenas
o turno, o que barateia fugir de uma pergunta fácil; o núcleo só aparece no mapa
depois de visitado; o santuário cura a cada visita; Maldição e Troca não têm alvo
no modo solo.

## Próximas rodadas propostas

1. **Balanceamento por playtests.** Ajustar tamanhos, tempo por pergunta,
   proporções de nível e pesos de cada tipo de sala; decidir as questões em
   aberto da rodada 4 depois de jogar partidas reais.
2. **Ritmo e identidade das salas.** Variações ambientais que ajudem a reconhecer
   setores e tornem cada tipo de sala legível na própria cena, não só no mapa.
3. **Qualidade do quiz.** Revisar respostas aceitas, categorias e o nível de cada
   pergunta; melhorar a explicação após erros sem quebrar o ritmo.
4. **Traduções.** Textos de tela e banco de perguntas em português, inglês e
   espanhol; os termos do código já seguem o glossário em inglês.
5. **Feedback audiovisual e acessibilidade.** Sons opcionais, anúncio de turnos
   pulados, controles de intensidade; revisar foco do teclado, contraste e
   leitura de estados.
6. **Modos especiais e multiplayer.** Movimento por dado, limite de turnos,
   desafios por seed e, mais adiante, partidas em rede com mapas separados. Cada
   modo entra em sua própria rodada.

Cada rodada deve terminar com uma versão jogável, verificação das regras que
mudaram e uma descrição objetiva do que foi concluído e do que ficou para depois.
