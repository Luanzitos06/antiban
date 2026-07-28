#!/data/data/com.termux/files/usr/bin/bash
# Instalador automático do AntiBan Resistência Forever no Termux

set -e

# Cores para o terminal
VERDE='\033[0;32m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
AZUL='\033[0;34m'
RESET='\033[0m'

echo -e "${AZUL}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${AZUL}║${RESET}     ${VERDE}🔥 ANTI BAN RESISTÊNCIA FOREVER - INSTALADOR${RESET}     ${AZUL}║${RESET}"
echo -e "${AZUL}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# 1. Atualizar pacotes do Termux
echo -e "${AMARELO}[1/5] Atualizando pacotes do Termux...${RESET}"
pkg update -y && pkg upgrade -y

# 2. Instalar dependências essenciais
echo -e "${AMARELO}[2/5] Instalando Python, Git e Screen...${RESET}"
pkg install python git screen -y

# 3. Clonar o repositório
REPO_URL="https://github.com/Luanzitos06/antiban.git"
DIR="antiban"

if [ -d "$DIR" ]; then
    echo -e "${AMARELO}[3/5] Diretório '$DIR' já existe. Atualizando...${RESET}"
    cd "$DIR"
    git pull
else
    echo -e "${AMARELO}[3/5] Clonando repositório...${RESET}"
    git clone "$REPO_URL"
    cd "$DIR"
fi

# 4. Dar permissão de execução ao start.py (caso necessário)
chmod +x start.py

# 5. Iniciar em segundo plano com screen
echo -e "${AMARELO}[4/5] Iniciando o sistema em uma sessão screen...${RESET}"
screen -dmS antiban bash -c "python start.py; exec bash"

echo ""
echo -e "${VERDE}✅ INSTALAÇÃO CONCLUÍDA!${RESET}"
echo ""
echo -e "${AZUL}📌 Comandos úteis:${RESET}"
echo -e "  ${VERDE}screen -r antiban${RESET}   → Para ver o que está acontecendo"
echo -e "  ${VERDE}Ctrl+A, D${RESET}           → Para desconectar (deixar rodando)"
echo -e "  ${VERDE}screen -X -S antiban quit${RESET} → Para encerrar o processo"
echo ""
echo -e "${AMARELO}⚠️  O script já está rodando em segundo plano.${RESET}"
echo -e "${AMARELO}   Use 'screen -r antiban' para acessar e digitar seu token.${RESET}"
