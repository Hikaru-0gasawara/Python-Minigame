#!/usr/bin/env bash
# Abre o ECOS no Linux, como o jogar.cmd no Windows. A entrada ECOS do menu (instalar.sh) chama este arquivo.
# Se o jogo não abrir e não houver um terminal à vista, o motivo aparece no terminal padrão.
pasta=$(dirname "$(readlink -f "$0")")

avisar() {
    if [ -t 2 ]; then
        printf '\n%s\n' "$1" >&2
    elif command -v x-terminal-emulator >/dev/null; then
        x-terminal-emulator -e bash -c 'printf "%s\n\n" "$1"; read -rp "Pressione Enter para fechar. "' ecos "$1"
    else
        printf '%s\n' "$1" >&2
    fi
    exit 1
}

python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null ||
    avisar "O ECOS precisa do Python 3.10 ou mais novo (comando python3)."
python3 -c 'import tkinter' 2>/dev/null ||
    avisar "Falta o Tkinter do Python. Instale com: sudo apt install python3-tk"

if [ -t 2 ]; then
    python3 "$pasta/src" || avisar "Não foi possível iniciar o ECOS. O erro está acima."
else
    erro=$(python3 "$pasta/src" 2>&1 >/dev/null) ||
        avisar "Não foi possível iniciar o ECOS:

$(printf '%s\n' "$erro" | tail -n 20)"
fi
