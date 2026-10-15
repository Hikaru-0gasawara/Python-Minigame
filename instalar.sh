#!/usr/bin/env bash
# Põe o ECOS no menu de aplicativos (Debian, Ubuntu, Pop!_OS): confere o Python e o Tkinter, desenha o
# ícone e cria a entrada ECOS, que abre o jogo desta pasta. Se mover a pasta, rode de novo.
#   bash instalar.sh            instala (ou atualiza a entrada)
#   bash instalar.sh --remover  tira a entrada e o ícone; os recordes ficam
set -e
pasta=$(dirname "$(readlink -f "$0")")
dados=${XDG_DATA_HOME:-$HOME/.local/share}
entrada=$dados/applications/ecos.desktop
icone=$dados/icons/hicolor/256x256/apps/ecos.png

if [ "$1" = --remover ]; then
    rm -f "$entrada" "$icone"
    echo "O ECOS saiu do menu. Os recordes continuam em $dados/ECOS."
    exit
fi

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
    echo "O ECOS precisa do Python 3.10 ou mais novo (comando python3). Instale com: sudo apt install python3"
    exit 1
fi
if ! python3 -c 'import tkinter' 2>/dev/null; then
    read -rp "Falta o Tkinter do Python (pacote python3-tk). Instalar agora? Vai pedir sua senha. [S/n] " resposta
    case $resposta in
        [nN]*) echo "Sem o Tkinter o jogo não abre. Instale depois com: sudo apt install python3-tk"; exit 1 ;;
    esac
    sudo apt install python3-tk
    python3 -c 'import tkinter'
fi

# A entrada guarda o caminho desta pasta entre aspas; estes caracteres exigiriam escapes que nem todo menu entende.
case $pasta in
    *[\"\`\$\\%]*) echo "O caminho da pasta tem \" \` \$ \\ ou %: mova o jogo para outra pasta e rode de novo."; exit 1 ;;
esac

chmod +x "$pasta/jogar.sh"       # um ZIP pode chegar sem a permissão de execução
mkdir -p "$(dirname "$entrada")" "$(dirname "$icone")"
python3 "$pasta/src/icon.py" "$icone"
cat > "$entrada" <<FIM
[Desktop Entry]
Type=Application
Name=ECOS
Comment=A Masmorra dos Ecos
Comment[en]=The Dungeon of Echoes
Exec="$pasta/jogar.sh"
Icon=$icone
Terminal=false
Categories=Game;
StartupWMClass=Ecos
FIM
echo "Pronto: o ECOS está no menu de aplicativos."
