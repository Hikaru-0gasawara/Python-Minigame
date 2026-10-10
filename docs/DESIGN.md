# Direção do quiz crawler

Este documento registra a direção do jogo e um roteiro para evoluí-lo parte por
parte. As etapas futuras são propostas; sua presença aqui não significa que já
foram implementadas. As rodadas 1 a 3 descrevem o crawler cooperativo, com
pontuação, combo e relógio compartilhados. A rodada 4 o transformou numa corrida
competitiva (ver [ADR-0001](adr/0001-competitive-race.md)) e removeu o
tabuleiro clássico ([ADR-0002](adr/0002-crawler-is-the-whole-game.md)). A
rodada 5 levou tudo para pixel art desenhada por código, dentro do mundo de ECO
([ADR-0004](adr/0004-pixel-art-drawn-by-code.md)), e passou a guardar
recordes ([ADR-0003](adr/0003-records-stored-locally.md)). O vocabulário do
domínio está em [CONTEXT.md](../CONTEXT.md).

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

## Identidade: dentro de ECO

A masmorra é o interior de um computador gigante que está morrendo, e ECO é a IA
que vive nele, inspirada em *I Have No Mouth, and I Must Scream*. Concreto,
ferrugem, cabos soltos, tubos fluorescentes falhando e telas de propaganda com o
olho de ECO fazem o cenário. Os guardiões são estátuas encapuzadas com uma tela
no rosto, por onde ECO provoca e pergunta. Escapar pelo núcleo é escapar de ECO.

O horror é sugerido, nunca explícito: a máquina oprime, ninguém sangra. As
provocações de ECO são curtas, frias e em português, e o jogo continua bom para
jogar no sofá com amigos.

O estilo é pixel art de 320×200 com 32 cores, no espírito de Risk of Rain, The
Binding of Isaac e Stardew Valley: tudo é desenhado pelo código, sem arquivos de
imagem, e ampliado em passos inteiros. A profundidade se lê pelo setor: concreto
frio e ciano perto da entrada, ferrugem e âmbar no meio, vermelho de alarme no
fundo. Ciano é a cor de ECO, e cada jogador tem a sua. Estados como baú aberto,
armadilha disparada ou guardião vencido também aparecem em texto ou na forma do
objeto, para nunca depender só da cor.

O ciclo é explorar, escolher uma rota, enfrentar o guardião, receber feedback e
decidir o próximo destino, numa corrida: cada jogador tem o próprio mapa, as
próprias vidas e o próprio poder guardado, e o primeiro a escapar vence. A
intensidade vem de retorno rápido: portas que abrem, o guardião que reage, sons
curtos. A pergunta e a resposta continuam legíveis durante os efeitos, e o
movimento reduzido transforma toda animação num corte imediato.

Os nomes Doom, Path of Exile, The Binding of Isaac, Megabonk, Vampire Survivors,
Vampire Crawlers, Dungeon Crawl e Math-Havoc foram indicados pelo usuário como
referências de intenção, e Risk of Rain, Isaac e Stardew Valley como referências
de visual. Não constituem uma lista de sistemas a copiar.

## Rodada 1: geografia da masmorra e hierarquia visual

Substituir o grafo de três faixas por uma planta de salas em coordenadas `(x, y)`.
Conexões correspondem a passagens entre vizinhos ortogonais. A distribuição pode
crescer em diferentes direções, com bifurcações, reencontros, ciclos e salas sem
saída. A aleatoriedade deve respeitar regras de conectividade e tamanho para que
a expedição sempre seja jogável.

O minimapa representa a mesma geografia usada na navegação, com revelação
progressiva, distinção entre sala atual, visitada e concluída, e conexões reais.
O jogador pode revisitar áreas concluídas e explorar ramos opcionais sem repetir
recompensas. A distância por caminhos desde a entrada é uma referência melhor
para progressão do que a antiga coluna de profundidade.

O destino final deve ser alcançável. Voltar de uma sala sem saída precisa ser possível; a
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

## Rodadas 2 e 3: menu e câmera

A rodada 2 deu ao menu uma identidade visual própria, e a rodada 3 desenhou as
salas em perspectiva com uma câmera que gira. A rodada 5 substituiu as duas
artes. Ficaram as regras da câmera e da travessia: quatro direções que portas,
botões e mapa acompanham; abrir e atravessar a porta antes de chegar; o desafio
seguinte só na chegada; ações duplicadas bloqueadas no caminho; o fim da expedição
cancela a travessia; olhar mantém a pergunta e o texto digitado.

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

## Rodada 5: pixel art e o mundo de ECO

Tudo o que o jogador vê passou a ser pixel art desenhada pelo código. Fora o
relógio da pergunta e o tempo da expedição, as regras não mudaram.

- **Tela:** um quadro de 320×200 com paleta fixa de 32 cores, ampliado pelo
  maior fator inteiro com faixas pretas. Toda a janela é a masmorra, com mapa no
  alto à direita e cartões dos jogadores embaixo. A resposta é digitada direto
  na caixa de diálogo, com fonte bitmap própria.
- **Setores:** raso, meio e fundo, pela profundidade em relação ao núcleo, cada
  um com paredes, tubos e estilo de porta próprios.
- **Salas com presença:** o guardião desperta, ouve na cor do jogador, falha ao
  ouvir um erro e sai do caminho quando vencido. Baús abrem, mímicos mordem,
  armadilhas disparam e ficam gastas, o santuário é uma cápsula de reparo e o
  núcleo é um portão com três travas. Decorações e partículas vêm da seed.
- **Portas e travessia:** a porta abre quadro a quadro, a câmera avança pelo vão
  em saltos de zoom e a sala nova chega escura, até os tubos acenderem.
- **ECO fala:** uma provocação e depois a pergunta, letra por letra, com bipe de
  voz. Mudança de regra: o tempo da pergunta só começa quando ela aparece
  inteira.
- **Som:** bipe, porta, baú, armadilha, acerto e erro, gerados pelo código, com
  mudo; fora do Windows, silêncio.
- **Recordes:** os cinco melhores tempos por dificuldade, guardados fora do
  repositório; a tela final avisa quando a fuga entra na lista.
- **Menu:** uma cena animada com torres em paralaxe, o núcleo de ECO pulsando, o
  título ECOS ao centro, as opções numa coluna e os recordes no canto,
  inteiramente usável pelo teclado.

## Próximas rodadas propostas

1. **Balanceamento por playtests.** Ajustar tamanhos, tempo por pergunta,
   proporções de nível e pesos de cada tipo de sala. Decidir as questões em
   aberto da rodada 4 (fuga barata, núcleo escondido, santuário repetido,
   Maldição e Troca no modo solo) depois de jogar expedições reais.
2. **Qualidade do quiz.** Revisar respostas aceitas, categorias e o nível de cada
   pergunta; melhorar a explicação após erros sem quebrar o ritmo.
3. **Traduções.** Textos de tela, provocações de ECO e banco de perguntas em
   português, inglês e espanhol; os termos do código já seguem o glossário em
   inglês.
4. **Música e acessibilidade.** Trilha e mixagem com mais de um som ao mesmo
   tempo, volume, anúncio de turnos pulados, revisão de foco do teclado e
   contraste, e suporte a controle.
5. **Modos especiais e multiplayer.** Movimento por dado, limite de turnos,
   desafios por seed e, mais adiante, expedições em rede com mapas separados. Cada
   modo entra em sua própria rodada.

Cada rodada deve terminar com uma versão jogável, verificação das regras que
mudaram e uma descrição objetiva do que foi concluído e do que ficou para depois.
