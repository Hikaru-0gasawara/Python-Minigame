"""The player's chosen language. On-screen text is written in Portuguese in the code; English is looked up here."""

LANGUAGES = {"pt": "PORTUGUÊS", "en": "ENGLISH"}
current = "pt"

EN = {
    # Difficulties
    "Aventureiro": "Adventurer", "Guerreiro": "Warrior", "Pesadelo": "Nightmare", "Campanha": "Campaign",
    # Buffs, Debuffs and penalties
    "−1 vida": "−1 life", "sem vidas, de volta à entrada": "no lives left, back to the entrance",
    "perde a próxima vez": "loses the next turn", "recua uma sala": "retreats one room",
    "+1 vida": "+1 life", "pressa: mais um movimento": "haste: one more move",
    "visão: salas a até 2 passos reveladas": "insight: rooms within 2 steps revealed",
    "escudo guardado": "ward held", "maldição guardada": "hex held", "troca guardada": "swap held",
    "o escudo anulou a penalidade": "the ward cancelled the penalty",
    "sala armada: ": "armed room: ",
    "maldição: J{n} perde a próxima vez": "hex: P{n} loses the next turn",
    "trocou de lugar com J{n}": "swapped places with P{n}",
    # Room kinds and their hints
    "Guardião": "Guardian", "Responda para passar": "Answer to pass",
    "Elite": "Elite", "Pergunta difícil · prêmio": "Hard question · reward",
    "Tesouro": "Treasure", "Um baú espera": "A chest awaits",
    "Mímico": "Mimic", "O baú mordeu!": "The chest bit!",
    "Armadilha": "Trap", "Já disparada": "Already sprung",
    "Santuário": "Sanctuary", "+1 vida a cada visita": "+1 life on every visit",
    "Sala vazia": "Empty room", "Nada aqui": "Nothing here",
    "Núcleo": "Core", "3 acertos para escapar": "3 hits to escape",
    "Entrada": "Entrance", "Ponto de partida": "Starting point",
    "Desconhecida": "Unknown", "O que há além?": "What lies beyond?",
    "Armada!": "Armed!", "Liberada": "Cleared",
    # Taunts
    "Mais um. Prove que ainda pensa.": "Another one. Prove you still think.",
    "Uma pergunta simples. Até para você.": "A simple question. Even for you.",
    "Responda, e talvez eu te deixe passar.": "Answer, and I might let you pass.",
    "Vejamos se você ainda raciocina.": "Let us see if you can still reason.",
    "Você hesita. Eu nunca hesito.": "You hesitate. I never hesitate.",
    "Cada erro seu me ensina algo.": "Every mistake of yours teaches me.",
    "Pense rápido. Eu já pensei por você.": "Think fast. I already thought for you.",
    "Outros pararam exatamente aqui.": "Others stopped exactly here.",
    "Esta eu guardei para os teimosos.": "I saved this one for the stubborn.",
    "Ninguém acertou esta em cem anos.": "No one has got this right in a century.",
    "Errar aqui custa caro. Tente.": "A mistake here costs dearly. Try.",
    "Vou gostar de ver você falhar.": "I will enjoy watching you fail.",
    "Eu sou a parede entre você e a saída.": "I am the wall between you and the exit.",
    "Fui feita para quebrar quem chega até aqui.": "I was made to break those who get this far.",
    "Acerte, e talvez eu sinta algo parecido com respeito.": "Get it right, and I may feel something like respect.",
    "Três verdades e você sai. Nenhuma mentira.": "Three truths and you leave. No lies.",
    "Ninguém escapa de mim. Prove o contrário.": "No one escapes me. Prove me wrong.",
    "Este é o meu núcleo. Fale com cuidado.": "This is my core. Speak carefully.",
    # Answers
    "Tempo da pergunta esgotado": "Time ran out", "Resposta incorreta": "Wrong answer", "Resposta": "Answer",
    "Escapou da masmorra!": "Escaped the dungeon!",
    "Guardião vencido. Passagem liberada.": "Guardian beaten. The way is open.", "Prêmio": "Reward",
    # The Expedition screen
    "Python Trivia • A Masmorra dos Ecos": "Python Trivia • The Dungeon of Echoes",
    "A entrada está segura. Clique numa porta ou use Alt + setas.":
        "The entrance is safe. Click a door or use Alt + arrows.",
    "Abrindo passagem…": "Opening the way…",
    "Caminho livre. A vez passa adiante.": "The way is clear. The turn passes on.",
    "J": "P", "ATRÁS": "BACK", "JOGADOR {n} · SUA VEZ": "PLAYER {n} · YOUR TURN",
    "MASMORRA CONQUISTADA": "DUNGEON CONQUERED", "JOGADOR {n} ESCAPOU": "PLAYER {n} ESCAPED",
    "SALA": "ROOM", "SALAS": "ROOMS",
    "N": "N", "L": "E", "S": "S", "O": "W", "NORTE": "NORTH", "LESTE": "EAST", "SUL": "SOUTH", "OESTE": "WEST",
    "FUJA": "RUN", "MENTE": "LIES", "NÃO!": "NO!", "OUVE": "HEARS", "SAÍDA?": "EXIT?", "|||| ||": "|||| ||",
    # The HUD
    "RASO": "SHALLOW", "MEIO": "MIDDLE", "FUNDO": "DEEP",
    "FÁCIL": "EASY", "MÉDIA": "MEDIUM", "DIFÍCIL": "HARD",
    "ESCUDO": "WARD", "MALDIÇÃO": "HEX", "TROCA": "SWAP",
    "REVANCHE · MESMA SEED": "REMATCH · SAME SEED", "NOVA SEED": "NEW SEED", "MENU": "MENU",
    "CONTINUAR": "RESUME", "SAIR PARA O MENU": "QUIT TO MENU", "PAUSA": "PAUSED",
    "VENCEU": "WON", "↶ RECUAR": "↶ RETREAT", "ESCUDO ANULA": "WARD BLOCKS", "ERRO": "MISS", "NÚCLEO": "CORE",
    "SOM": "SOUND", "NOVO RECORDE": "NEW RECORD",
    "Compartilhe a seed para desafiar alguém.": "Share the seed to challenge someone.",
    # The menu
    "DIFICULDADE": "DIFFICULTY", "JOGADORES": "PLAYERS", "SEED": "SEED", "MOVIMENTO": "MOTION", "IDIOMA": "LANGUAGE",
    "ALEATÓRIA": "RANDOM", "MUDO": "MUTED", "LIGADO": "ON", "COMPLETO": "FULL", "REDUZIDO": "REDUCED",
    "ENTRAR →": "ENTER →", "JOGAR": "PLAY", "CONFIGURAÇÕES": "SETTINGS", "SAIR": "QUIT", "← VOLTAR": "← BACK",
    "MÚSICA": "MUSIC", "LIGADA": "ON", "DESLIGADA": "OFF", "↑↓ ENTER · F1 AJUDA": "↑↓ ENTER · F1 HELP",
    "BANCO DE PERGUNTAS INCOMPLETO": "QUESTION BANK INCOMPLETE",
    "POR PERGUNTA": "PER QUESTION", "↑↓ ←→ ENTER · F1 AJUDA": "↑↓ ←→ ENTER · F1 HELP",
    "RECORDES": "RECORDS", "Nenhuma fuga ainda.": "No escapes yet.",
    "A MASMORRA DOS ECOS": "THE DUNGEON OF ECHOES",
    "Como jogar · ECOS": "How to play · ECOS", "CADA RESPOSTA ABRE UM CAMINHO": "EVERY ANSWER OPENS A PATH",
    "01  EXPLORE": "01  EXPLORE",
    "Um movimento por turno; seu mapa mostra só o que você descobriu.\nAlt + setas: mover. Alt + Q/E: olhar para os lados.":
        "One move per turn; your map shows only what you have discovered.\nAlt + arrows: move. Alt + Q/E: look around.",
    "02  RESPONDA": "02  ANSWER",
    "Cada guardião pergunta a todo jogador que entra. Você tem 3 vidas.\nErrar fácil: −1 vida · média: perde a vez · difícil: recua.":
        "Every guardian questions each player who enters. You have 3 lives.\nMissing easy: −1 life · medium: lose a turn · hard: retreat.",
    "03  ESCAPE PRIMEIRO": "03  ESCAPE FIRST",
    "Acerte 3 perguntas do núcleo, uma por turno.\nO primeiro jogador a escapar vence a corrida.":
        "Answer 3 of the core's questions, one per turn.\nThe first player to escape wins the race.",
    "ENTENDI   →": "GOT IT   →",
}


def t(text):
    """The text in the chosen language; a missing translation is a KeyError, caught by tests/test_lang.py."""
    return EN[text] if current == "en" else text
