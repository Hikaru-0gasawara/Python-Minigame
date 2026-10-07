# Direção do quiz crawler

Este documento registra a direção desta rodada e um roteiro para evoluir o jogo
parte por parte. As etapas futuras são propostas; sua presença aqui não significa
que já foram implementadas.

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

O ciclo é explorar, escolher uma rota, resolver o desafio, receber feedback e
decidir o próximo destino. Pontuação, combo, bônus de velocidade, vidas e tempo
formam a base existente a preservar enquanto a exploração ganha profundidade.
Retratos ou perfis dos participantes devem servir para identificar o jogador da
vez e a pontuação individual, sem acrescentar painéis vazios de inventário.

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

## Próximas rodadas propostas

1. **Ritmo e identidade das salas.** Ajustar distâncias, duração da expedição,
   densidade de eventos e linguagem das salas após experimentar o novo mapa.
   Criar variações ambientais que ajudem a reconhecer setores.
2. **Progressão dentro da partida.** Introduzir escolhas de melhorias com efeitos
   claros sobre tempo, pontuação ou risco. Definir limites e testar combinações
   antes de ampliar a quantidade de poderes.
3. **Qualidade do quiz.** Revisar respostas aceitas, categorias e dificuldade;
   planejar localização do banco atualmente em inglês. Melhorar a explicação
   após erros sem quebrar o ritmo.
4. **Feedback audiovisual e acessibilidade.** Sons opcionais, transições curtas,
   destaque de sequência e controles de intensidade; revisar foco do teclado,
   contraste e leitura de estados.
5. **Continuidade entre partidas.** Histórico de resultados, perfis e desafios
   reproduzíveis por semente, caso essas funções façam sentido após testar o
   ciclo principal. Qualquer progressão persistente exige decisão própria.

Cada rodada deve terminar com uma versão jogável, verificação das regras que
mudaram e uma descrição objetiva do que foi concluído e do que ficou para depois.
